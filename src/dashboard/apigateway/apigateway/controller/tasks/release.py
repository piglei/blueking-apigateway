#
# TencentBlueKing is pleased to support the open source community by making
# 蓝鲸智云 - API 网关(BlueKing - APIGateway) available.
# Copyright (C) 2017 THL A29 Limited, a Tencent company. All rights reserved.
# Licensed under the MIT License (the "License"); you may not use this file except
# in compliance with the License. You may obtain a copy of the License at
#
#     http://opensource.org/licenses/MIT
#
# Unless required by applicable law or agreed to in writing, software distributed under
# the License is distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND,
# either express or implied. See the License for the specific language governing permissions and
# limitations under the License.
#
# We undertake not to change the open source license (MIT license) applicable
# to the current version of the project delivered to anyone in the future.
#
import logging
from typing import Optional

from celery import shared_task

from apigateway.common.event.event import PublishEventReporter
from apigateway.controller.distributor.base import BaseDistributor
from apigateway.controller.distributor.etcd import EtcdDistributor
from apigateway.controller.distributor.helm import HelmDistributor
from apigateway.controller.helm.chart import ChartHelper
from apigateway.controller.helm.release import ReleaseHelper
from apigateway.controller.procedure_logger.release_logger import ReleaseProcedureLogger
from apigateway.core.constants import ReleaseStatusEnum
from apigateway.core.models import MicroGateway, MicroGatewayReleaseHistory, Release

logger = logging.getLogger(__name__)


def _release_gateway(
    distributor: BaseDistributor,
    micro_gateway_release_history_id: int,
    release: Release,
    micro_gateway: MicroGateway,
    procedure_logger: ReleaseProcedureLogger,
):
    """发布资源到微网关"""
    procedure_logger.info(f"release begin, micro_gateway_release_history_id({micro_gateway_release_history_id})")
    release_history_qs = MicroGatewayReleaseHistory.objects.filter(id=micro_gateway_release_history_id)
    latest_micro_gateway_release_history = release_history_qs.last()
    # 表明发布已开始
    release_history_qs.update(status=ReleaseStatusEnum.RELEASING.value)
    # add publish event
    PublishEventReporter.report_create_publish_task_success_event(
        latest_micro_gateway_release_history.release_history, release.stage
    )
    PublishEventReporter.report_distribute_configuration_doing_event(
        latest_micro_gateway_release_history.release_history, release.stage
    )
    try:
        is_success, fail_msg = distributor.distribute(
            release=release,
            micro_gateway=micro_gateway,
            release_task_id=procedure_logger.release_task_id,
            publish_id=latest_micro_gateway_release_history.release_history_id,
        )
        if is_success:
            PublishEventReporter.report_distribute_configuration_success_event(
                latest_micro_gateway_release_history.release_history, release.stage
            )

        else:
            PublishEventReporter.report_distribute_configuration_failure_event(
                latest_micro_gateway_release_history.release_history, release.stage, fail_msg
            )
            return False
    except Exception as err:
        # 记录失败原因
        procedure_logger.exception("release failed")
        # 上报失败事件
        PublishEventReporter.report_distribute_configuration_failure_event(
            latest_micro_gateway_release_history.release_history, release.stage, f"error: {err}"
        )
        # 异常抛出，让 celery 停止编排
        raise

    return True


@shared_task(ignore_result=True)
def release_gateway_by_helm(access_token: str, username, release_id, micro_gateway_release_history_id):
    """发布资源到专享网关"""
    logger.info(
        "release_gateway_by_helm: release_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_release_history_id,
    )
    release = Release.objects.prefetch_related("stage", "gateway", "resource_version").get(id=release_id)
    stage = release.stage
    micro_gateway = stage.micro_gateway
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_helm",
        logger=logger,
        gateway=release.gateway,
        stage=stage,
        micro_gateway=micro_gateway,
    )
    # 环境未绑定微网关
    if not micro_gateway:
        procedure_logger.warning("stage not bound to a micro-gateway, cannot release by helm.")
        return False

    # BkGatewayConfig 随着 micro-gateway 的 release 下发，所以无需包含
    return _release_gateway(
        distributor=HelmDistributor(
            chart_helper=ChartHelper(access_token=access_token),
            release_helper=ReleaseHelper(access_token=access_token),
            generate_chart=True,
            operator=username,
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )


@shared_task(ignore_result=True)
def release_gateway_by_registry(
    micro_gateway_id, release_id, micro_gateway_release_history_id, publish_id: Optional[int] = None
):
    """发布资源到共享网关，为了使得类似环境变量等引用生效，同时会将所有配置都进行同步"""
    logger.info(
        "release_gateway_by_etcd: release_id=%s, micro_gateway_id=%s, micro_gateway_release_history_id=%s",
        release_id,
        micro_gateway_id,
        micro_gateway_release_history_id,
    )
    release = Release.objects.prefetch_related("stage", "gateway", "resource_version").get(id=release_id)
    micro_gateway = MicroGateway.objects.get(id=micro_gateway_id, is_shared=True)
    # 如果是共享实例对应的网关发布，同时将对应的实例资源下发
    include_gateway_global_config = release.gateway_id == micro_gateway.gateway_id
    procedure_logger = ReleaseProcedureLogger(
        "release_gateway_by_etcd",
        logger=logger,
        gateway=release.gateway,
        stage=release.stage,
        micro_gateway=micro_gateway,
        release_task_id=micro_gateway_release_history_id,
        publish_id=publish_id,
    )
    return _release_gateway(
        distributor=EtcdDistributor(
            include_gateway_global_config=include_gateway_global_config,
        ),
        micro_gateway_release_history_id=micro_gateway_release_history_id,
        release=release,
        micro_gateway=micro_gateway,
        procedure_logger=procedure_logger,
    )
