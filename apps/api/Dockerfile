FROM golang:1.24-alpine AS builder

WORKDIR /src
COPY go.work .
COPY packages ./packages
COPY apps ./apps

WORKDIR /src/apps/api
RUN go build -o /bin/api .

FROM alpine:latest
WORKDIR /app
COPY --from=builder /bin/api .
EXPOSE 8000
CMD ["./api"]
