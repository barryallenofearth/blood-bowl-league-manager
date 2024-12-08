if ($(docker buildx ls | Select-String -Pattern 'multi-arch-builder')){
    docker buildx create --name
}

docker buildx use multi-arch-builder
docker buildx build -t barryallenofearth/blood-bowl-league-manager:$($args[0]) --platform linux/arm64,linux/amd64 --push .