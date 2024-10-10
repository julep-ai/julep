variable "TAG" {
  default = "..."
}

variable "GIT_SHA" {
  default = "..."
}

group "default" {
  targets = [
    "agents-api",
    "agents-api-worker",
    "cozo-migrate",
    "memory-store",
    "integrations",
    "gateway",
  ]
}

target "agents-api" {
  context = "./agents-api"
  dockerfile = "Dockerfile"
  tags = [
    "julepai/agents-api:${TAG}",
    "julepai/agents-api:git-${GIT_SHA}"
  ]
}

target "agents-api-worker" {
  context = "./agents-api"
  dockerfile = "Dockerfile.worker"
  tags = [
    "julepai/worker:${TAG}",
    "julepai/worker:git-${GIT_SHA}"
  ]
}

target "cozo-migrate" {
  context = "./agents-api"
  dockerfile = "Dockerfile.migration"
  tags = [
    "julepai/cozo-migrate:${TAG}",
    "julepai/cozo-migrate:git-${GIT_SHA}"
  ]
}

target "memory-store" {
  context = "./memory-store"
  dockerfile = "Dockerfile"
  tags = [
    "julepai/memory-store:${TAG}",
    "julepai/memory-store:git-${GIT_SHA}"
  ]
}

target "integrations" {
  context = "./integrations-service"
  dockerfile = "Dockerfile"
  tags = [
    "julepai/integrations:${TAG}",
    "julepai/integrations:git-${GIT_SHA}"
  ]
}

target "gateway" {
  context = "./gateway"
  dockerfile = "Dockerfile"
  tags = [
    "julepai/gateway:${TAG}",
    "julepai/gateway:git-${GIT_SHA}"
  ]
}