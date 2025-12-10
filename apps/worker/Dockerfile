FROM golang:1.24-alpine AS builder

WORKDIR /src
COPY go.work .
COPY packages ./packages
COPY apps ./apps

WORKDIR /src/apps/worker
RUN go build -o /bin/worker .

FROM alpine:latest
# Install Docker CLI to support Docker-in-Docker or sibling docker access (though Go SDK uses socket directly, CLI is useful for debugging)
RUN apk add --no-cache docker-cli

WORKDIR /app
COPY --from=builder /bin/worker .
CMD ["./worker"]
