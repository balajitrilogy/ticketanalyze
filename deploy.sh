#!/bin/bash

# AWS Configuration
AWS_REGION="us-east-1"  # Change to your preferred region
ECR_REPOSITORY_NAME="skyvera-ticket-analysis"
ECS_CLUSTER_NAME="skyvera-cluster"
ECS_SERVICE_NAME="skyvera-ticket-analysis-service"

# Create ECR repository if it doesn't exist
aws ecr create-repository --repository-name $ECR_REPOSITORY_NAME --region $AWS_REGION || true

# Get ECR repository URI
ECR_REPOSITORY_URI=$(aws ecr describe-repositories --repository-names $ECR_REPOSITORY_NAME --region $AWS_REGION --query 'repositories[0].repositoryUri' --output text)

# Authenticate Docker to ECR
aws ecr get-login-password --region $AWS_REGION | docker login --username AWS --password-stdin $ECR_REPOSITORY_URI

# Build and push Docker image
docker build -t $ECR_REPOSITORY_NAME .
docker tag $ECR_REPOSITORY_NAME:latest $ECR_REPOSITORY_URI:latest
docker push $ECR_REPOSITORY_URI:latest

# Update task definition
sed -i "s|\${ECR_REPOSITORY_URI}|$ECR_REPOSITORY_URI|g" task-definition.json
sed -i "s|\${AWS_REGION}|$AWS_REGION|g" task-definition.json

# Register new task definition
TASK_DEFINITION_ARN=$(aws ecs register-task-definition --cli-input-json file://task-definition.json --region $AWS_REGION --query 'taskDefinition.taskDefinitionArn' --output text)

# Update ECS service
aws ecs update-service \
    --cluster $ECS_CLUSTER_NAME \
    --service $ECS_SERVICE_NAME \
    --task-definition $TASK_DEFINITION_ARN \
    --region $AWS_REGION 