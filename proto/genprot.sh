#!/bin/bash
echo "Generating proocol"
python3 -m grpc_tools.protoc -I=proto/ --python_out=proto/ --grpc_python_out=proto/ proto/alliance.proto
echo "DONE"
