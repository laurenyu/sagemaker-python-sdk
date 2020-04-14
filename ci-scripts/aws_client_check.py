# Copyright 2020 Amazon.com, Inc. or its affiliates. All Rights Reserved.
#
# Licensed under the Apache License, Version 2.0 (the "License"). You
# may not use this file except in compliance with the License. A copy of
# the License is located at
#
#     http://aws.amazon.com/apache2.0/
#
# or in the "license" file accompanying this file. This file is
# distributed on an "AS IS" BASIS, WITHOUT WARRANTIES OR CONDITIONS OF
# ANY KIND, either express or implied. See the License for the specific
# language governing permissions and limitations under the License.
from __future__ import absolute_import

import astroid

from pylint.interfaces import IAstroidChecker
from pylint.checkers import BaseChecker


class NoGlobalS3Endpoint(BaseChecker):
    """Checker to ensure that the (default) S3 global endpoint is not used for
    boto3 clients or resources.

    This checks for the following calls:

        .. code::
            boto3.client("s3")
            boto3.resource("s3")
            boto_session.client("s3")
            boto_session.resource("s3")

    If any of the above calls are made with specifying ``region_name`` or
    ``endpoint_url``, the checker adds the message "s3-with-global-endpoint".
    """
    __implements__ = IAstroidChecker

    name = "no-global-s3-endpoint"
    priority = -1

    msgs = {
        "C0001": (
            "S3 client or resource is instantiated without region_name or endpoint_url.",
            "s3-with-global-endpoint",
            "The parameter region_name or endpoint_url should be provided to the boto3 function.",
        ),
    }
    options = ()

    def visit_call(self, node):
        """Visit each call and check if it is instantiating
        an S3 client or resource. If so, check that either
        ``region_name`` or ``endpoint_url`` is specified.
        If not, add the message "s3-with-global-endpoint".
        """
        if self._is_s3_client_or_resource(node):
            if node.keywords is not None:
                for kwarg in node.keywords:
                    if self._kwarg_present(kwarg, "region_name"):
                        return
                    if self._kwarg_present(kwarg, "endpoint_url"):
                        return

            self.add_message("s3-with-global-endpoint", node=node)

    def _is_s3_client_or_resource(self, node):
        return isinstance(node.func, astroid.Attribute) and \
            self._is_boto_client_or_resource(node) and \
            node.args[0].value == "s3"

    def _is_boto_client_or_resource(self, node):
        if not hasattr(node, "func"):
            return False

        if hasattr(node.func.expr, "name") and \
           node.func.expr.name in ("boto3", "boto_session") and \
           node.func.attrname in ("client", "resource"):
            return True

        while hasattr(node, "expr"):
            next_node = node.expr
            if next_node.attrname in ("boto3", "boto_session"):
                if node.attrname in ("client", "resource"):
                    return True
            node = next_node

        return False

    def _kwarg_present(self, kwarg, name_to_check):
        return kwarg.arg == name_to_check and kwarg.value


def register(linter):
    """Auto-register the implemented checkers"""
    linter.register_checker(NoGlobalS3Endpoint(linter))
