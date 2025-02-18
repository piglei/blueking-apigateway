# -*- coding: utf-8 -*-
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

from drf_yasg.utils import swagger_auto_schema
from rest_framework import generics, status

from apigateway.apps.audit.constants import OpTypeEnum
from apigateway.apps.label.models import APILabel
from apigateway.biz.gateway_label import GatewayLabelHandler
from apigateway.utils.responses import OKJsonResponse

from .serializers import GatewayLabelInputSLZ, GatewayLabelOutputSLZ


class GatewayLabelListCreateApi(generics.ListCreateAPIView):
    serializer_class = GatewayLabelInputSLZ

    def get_queryset(self):
        return APILabel.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(
        responses={status.HTTP_200_OK: GatewayLabelOutputSLZ(many=True)},
        tags=["WebAPI.GatewayLabel"],
    )
    def list(self, request, *args, **kwargs):
        queryset = self.get_queryset()
        slz = GatewayLabelOutputSLZ(queryset, many=True)
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_201_CREATED: ""}, request_body=GatewayLabelInputSLZ, tags=["WebAPI.GatewayLabel"]
    )
    def create(self, request, gateway_id):
        slz = self.get_serializer(data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            created_by=request.user.username,
            updated_by=request.user.username,
        )

        GatewayLabelHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.CREATE,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
        )

        return OKJsonResponse(status=status.HTTP_201_CREATED)


class GatewayLabelRetrieveUpdateDestroyApi(generics.RetrieveUpdateDestroyAPIView):
    serializer_class = GatewayLabelInputSLZ
    lookup_field = "id"

    def get_queryset(self):
        return APILabel.objects.filter(api=self.request.gateway)

    @swagger_auto_schema(responses={status.HTTP_200_OK: GatewayLabelOutputSLZ()}, tags=["WebAPI.GatewayLabel"])
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = GatewayLabelOutputSLZ(instance)
        return OKJsonResponse(data=slz.data)

    @swagger_auto_schema(
        responses={status.HTTP_204_NO_CONTENT: ""}, request_body=GatewayLabelInputSLZ, tags=["WebAPI.GatewayLabel"]
    )
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        slz = self.get_serializer(instance, data=request.data)
        slz.is_valid(raise_exception=True)

        slz.save(
            updated_by=request.user.username,
        )

        GatewayLabelHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.MODIFY,
            instance_id=slz.instance.id,
            instance_name=slz.instance.name,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)

    @swagger_auto_schema(responses={status.HTTP_204_NO_CONTENT: ""}, tags=["WebAPI.APILabels"])
    def destroy(self, request, *args, **kwargs):
        instance = self.get_object()
        instance_id = instance.id

        instance.delete()

        GatewayLabelHandler.record_audit_log_success(
            username=request.user.username,
            gateway_id=request.gateway.id,
            op_type=OpTypeEnum.DELETE,
            instance_id=instance_id,
            instance_name=instance.name,
        )

        return OKJsonResponse(status=status.HTTP_204_NO_CONTENT)
