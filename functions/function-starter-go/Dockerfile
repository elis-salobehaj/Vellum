# Syntax: docker/dockerfile:1

# Build the function binary
FROM golang:1.25.5 AS builder
WORKDIR /workspace

# Copy the Go Modules manifests
COPY go.mod go.sum ./
# cache deps before building and copying source so that we don't need to re-download as much
# and so that source changes don't invalidate our downloaded layer
RUN go mod download

# Copy the go source
COPY main.go main.go

# Build
# -a: force rebuilding of packages that are already up-to-date.
# -o: output file name
RUN CGO_ENABLED=0 GOOS=linux go build -a -o function main.go

# Use distroless as minimal base image to package the function binary
# Refer to https://github.com/GoogleContainerTools/distroless for more details
FROM gcr.io/distroless/static:nonroot
WORKDIR /
COPY --from=builder /workspace/function .
USER 65532:65532

ENTRYPOINT ["/function"]
