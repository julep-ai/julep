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
    "memory-store",
    "integrations",
    "gateway",
    "blob-store",
//    "code-interpreter",
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

target "blob-store" {
  context = "./blob-store"
  dockerfile = "Dockerfile"
  tags = [
    "julepai/blob-store:${TAG}",
    "julepai/blob-store:git-${GIT_SHA}"
  ]
}

// target "code-interpreter" {
//  context = "./code-interpreter/vendor/cohere-ai/cohere-terrarium"
//  dockerfile = "Dockerfile"
//  tags = [
//    "julepai/code-interpreter:${TAG}",
//    "julepai/code-interpreter:git-${GIT_SHA}"
//  ]
// }
