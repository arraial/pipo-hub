variable "ARCHS" {
  default = ["linux/amd64", "linux/arm64"]
}

variable "IMAGE" {
  default = "pipo_hub"
}

variable "PYTHON_VERSION" {
  default = "3.13.3"
}

variable "POETRY_VERSION" {
  default = "2.1.2"
}

variable "TAG" {
  default = "0.0.0"
}

variable "GITHUB_REPOSITORY_OWNER" {
  default = "arraial"
}

target "_common" {
  args = {
    PROGRAM_VERSION = TAG
    PYTHON_VERSION = PYTHON_VERSION
    POETRY_VERSION = POETRY_VERSION
    BUILDKIT_CONTEXT_KEEP_GIT_DIR = 1
  }
  tags = [
    "${GITHUB_REPOSITORY_OWNER}/${IMAGE}:${TAG}",
    "${GITHUB_REPOSITORY_OWNER}/${IMAGE}:latest"
  ]
  labels = {
    "org.opencontainers.image.version" = "${TAG}"
    "org.opencontainers.image.authors" = "https://github.com/${GITHUB_REPOSITORY_OWNER}"
    "org.opencontainers.image.source" = "https://github.com/${GITHUB_REPOSITORY_OWNER}/pipo-hub"
  }
}

target "docker-metadata-action" {}

group "default" {
  targets = ["image-local"]
}

target "image-local" {
  inherits = ["_common"]
  context = "."
  dockerfile = "Dockerfile"
  output = ["type=docker"]
}

target "test" {
  target = "test"
  inherits = ["image-local"]
  output = ["type=cacheonly"]
}

target "image-arch" {
  inherits = ["image-local", "docker-metadata-action"]
  output = ["type=registry"]
  sbom = true
  platforms = ARCHS
  cache-from = flatten([
    for arch in ARCHS : "type=registry,ref=${GITHUB_REPOSITORY_OWNER}/${IMAGE}:buildcache-${replace(arch, "/", "-")}"
  ])
}

target "image-arch-cache" {
  name = "image-arch-cache-${replace(arch, "/", "-")}"
  inherits = ["image-local", "docker-metadata-action"]
  output = ["type=cacheonly"]
  cache-from = ["type=registry,ref=${GITHUB_REPOSITORY_OWNER}/${IMAGE}:buildcache-${replace(arch, "/", "-")}"]
  cache-to = ["type=registry,ref=${GITHUB_REPOSITORY_OWNER}/${IMAGE}:buildcache-${replace(arch, "/", "-")},mode=max,oci-mediatypes=true,image-manifest=true"]
  platform = arch
  matrix = {
    arch = ARCHS
  }
  depends = ["image-arch"]
}

group "image-all" {
  targets = ["image-arch", "image-arch-cache"]
}
