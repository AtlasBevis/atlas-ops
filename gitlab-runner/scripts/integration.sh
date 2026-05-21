#!/bin/bash

# Two types of provision methods are supported:
# - Authentication Token set directly in the values.yaml (authentication)
# - Authentication Token set via a secret (secret)
tokenProvisionMethod=$1
token=$2
valueYamlPath=$3

INTEGRATION_RUNNER_NAME=${INTEGRATION_RUNNER_NAME:-integration-runner}
INTEGRATION_HELM_POD_RELEASE_LABEL=${INTEGRATION_HELM_POD_RELEASE_LABEL:-release=$INTEGRATION_RUNNER_NAME}

case $tokenProvisionMethod in
    "plaintext")
        helm install -f "$valueYamlPath" --timeout 5m --wait --set gitlabUrl="$CI_SERVER_URL",runnerToken="$token" "$INTEGRATION_RUNNER_NAME" .
        ;;
    "secret")
        cat <<EOF > secret.yaml
apiVersion: v1
kind: Secret
metadata:
  name: gitlab-runner-secret
type: Opaque
stringData:
  runner-token: $token
  runner-registration-token: ""
EOF

        kubectl apply -f secret.yaml
        rm secret.yaml

        helm install -f "$valueYamlPath" --timeout 5m --wait --set gitlabUrl="$CI_SERVER_URL",runners.secret="gitlab-runner-secret" "$INTEGRATION_RUNNER_NAME" .
        ;;
    *)
        echo "Token provided is not supported"
        exit 1
        ;;
esac

kubectl describe pod -l "$INTEGRATION_HELM_POD_RELEASE_LABEL"

timeout 60s grep -m1 "Starting multi-runner" <(kubectl logs -f -l "$INTEGRATION_HELM_POD_RELEASE_LABEL" --tail=-1)

exit_code="$?"

kubectl logs --tail=-1 -l "$INTEGRATION_HELM_POD_RELEASE_LABEL"

exit $exit_code

