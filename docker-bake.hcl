variable "ARCHS" {
  default = ["linux/amd64", "linux/arm64"]
}

variable "IMAGE" {
  default = "pipo_hub"
}

variable "PYTHON_VERSION" {
  default = "3.13"
}

variable "UV_VERSION" {
  default = "0.9.18"
}

variable "TAG" {
  default = "local"
}

variable "GITHUB_REPOSITORY_OWNER" {
  default = "arraial"
}

target "_common" {
  args = {
    APP_VERSION = TAG
    PYTHON_VERSION = PYTHON_VERSION
    UV_VERSION = UV_VERSION
    BUILDKIT_CONTEXT_KEEP_GIT_DIR = 1
  }
  tags = [
    "${GITHUB_REPOSITORY_OWNER}/${IMAGE}:latest",
    "${GITHUB_REPOSITORY_OWNER}/${IMAGE}:${TAG}"
  ]
  labels = {
    "org.opencontainers.image.version" = "${TAG}"
    "org.opencontainers.image.authors" = "https://github.com/${GITHUB_REPOSITORY_OWNER}"
    "org.opencontainers.image.source" = "https://github.com/${GITHUB_REPOSITORY_OWNER}/pipo-hub"
  }
}

target "docker-metadata-action" {}

group "default" {
  targets = ["image"]
}

target "image" {
  inherits = ["_common"]
  context = "."
  dockerfile = "Dockerfile"
  output = ["type=docker"]
}

target "test" {
  target = "test"
  inherits = ["image"]
  output = ["type=docker"]
  tags = [
    "${IMAGE}:test"
  ]
}

target "image-arch" {
  inherits = ["image", "docker-metadata-action"]
  output = ["type=registry"]
  sbom = true
  platforms = ARCHS
  cache-from = flatten([
    for arch in ARCHS : "type=registry,ref=${GITHUB_REPOSITORY_OWNER}/${IMAGE}:buildcache-${replace(arch, "/", "-")}"
  ])
}

target "image-arch-cache" {
  name = "image-arch-cache-${replace(arch, "/", "-")}"
  inherits = ["image", "docker-metadata-action"]
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
