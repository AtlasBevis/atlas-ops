# Grpc Rust


## Installments

Ubuntu: install protobuf

```sh
sudo apt update && sudo apt upgrade -y
sudo apt install -y protobuf-compiler libprotobuf-dev
```

1. Add dependencies

```sh
# if you want latest version
cargo add tonic tonic-prost prost 

# or pin version
cargo add tonic@0.14.6 tonic-prost@0.14.6 prost@0.14.4
```

2. Add build dependencies

```sh
cargo add --build tonic-prost-build@0.14.6 prost-build@0.14.4 protoc-bin-vendored@3
```

## How to write Proto


## References

- [Install](https://grpc.io/docs/languages/rust/quickstart/)