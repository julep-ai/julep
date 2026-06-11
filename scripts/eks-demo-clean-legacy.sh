#!/usr/bin/env bash
set -euo pipefail

AWS_REGION="${AWS_REGION:-us-east-1}"
CLUSTER_NAME="${CLUSTER_NAME:-julep-v2-auto-20260610}"
ECR_REPO="${ECR_REPO:-ca-worker-llm-demo}"
CLUSTER_ROLE="${CLUSTER_ROLE:-JulepV2EksAutoClusterRole}"
NODE_ROLE="${NODE_ROLE:-JulepV2EksAutoNodeRole}"

if aws eks describe-cluster --region "$AWS_REGION" --name "$CLUSTER_NAME" >/dev/null 2>&1; then
  aws eks update-kubeconfig --region "$AWS_REGION" --name "$CLUSTER_NAME" --alias "$CLUSTER_NAME" >/dev/null || true
  kubectl delete namespace julep-demo temporal keda --ignore-not-found=true --wait=false || true
  aws eks delete-cluster --region "$AWS_REGION" --name "$CLUSTER_NAME" >/dev/null
  aws eks wait cluster-deleted --region "$AWS_REGION" --name "$CLUSTER_NAME"
fi

if aws ecr describe-repositories --region "$AWS_REGION" --repository-names "$ECR_REPO" >/dev/null 2>&1; then
  aws ecr delete-repository --region "$AWS_REGION" --repository-name "$ECR_REPO" --force >/dev/null
fi

for pair in \
  "$CLUSTER_ROLE AmazonEKSClusterPolicy" \
  "$CLUSTER_ROLE AmazonEKSComputePolicy" \
  "$CLUSTER_ROLE AmazonEKSBlockStoragePolicy" \
  "$CLUSTER_ROLE AmazonEKSLoadBalancingPolicy" \
  "$CLUSTER_ROLE AmazonEKSNetworkingPolicy" \
  "$NODE_ROLE AmazonEKSWorkerNodeMinimalPolicy" \
  "$NODE_ROLE AmazonEC2ContainerRegistryPullOnly"; do
  set -- $pair
  aws iam detach-role-policy \
    --role-name "$1" \
    --policy-arn "arn:aws:iam::aws:policy/$2" >/dev/null 2>&1 || true
done

aws iam delete-role --role-name "$CLUSTER_ROLE" >/dev/null 2>&1 || true
aws iam delete-role --role-name "$NODE_ROLE" >/dev/null 2>&1 || true

echo "Legacy demo resources removed if they existed."
