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
from typing import List

from apigateway.core.constants import (
    GatewayStatusEnum,
    PublishSourceEnum,
    StageStatusEnum,
)
from apigateway.core.models import Release, ReleaseHistory


class ReleaseHandler:
    @staticmethod
    def get_released_stage_ids(gateway_ids: List[int]) -> List[int]:
        return list(
            Release.objects.filter(
                gateway_id__in=gateway_ids,
                gateway__status=GatewayStatusEnum.ACTIVE.value,
                stage__status=StageStatusEnum.ACTIVE.value,
            ).values_list("stage_id", flat=True)
        )

    @staticmethod
    def save_release_history(release: Release, source: PublishSourceEnum, author: str) -> ReleaseHistory:
        """保存发布历史"""
        release_history = ReleaseHistory.objects.create(
            gateway=release.gateway,
            stage=release.stage,
            source=source.value,
            resource_version=release.resource_version,
            created_by=author,
        )
        return release_history

    @staticmethod
    def save_release_history_with_id(
        gateway_id: int, stage_id: int, resource_version_id: int, source: PublishSourceEnum, author: str
    ) -> ReleaseHistory:
        """保存发布历史"""
        release_history = ReleaseHistory.objects.create(
            gateway_id=gateway_id,
            stage_id=stage_id,
            source=source.value,
            resource_version_id=resource_version_id,
            created_by=author,
        )
        return release_history
