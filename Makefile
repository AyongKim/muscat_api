DOCKER_REPOSITORY = 692924884361.dkr.ecr.ap-northeast-2.amazonaws.com
DOCKER_IMAGE_NAME = all-class-api-server
DOCKER_IMAGE = $(DOCKER_REPOSITORY)/$(DOCKER_IMAGE_NAME)
DOCKER_TAG   ?=dev

.PHONY: build-docker-image
build:
	docker build -t $(DOCKER_IMAGE):$(DOCKER_TAG) .

.PHONY: run-single-container
run:
	docker run --rm -it \
    -p 1001:1001 \
    --name all-class-api-server \
    $(DOCKER_IMAGE):$(DOCKER_TAG)

.PHONY: push-docker-image
push:
	docker push $(DOCKER_IMAGE):$(DOCKER_TAG)
