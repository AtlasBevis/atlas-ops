# name app build
APP_NAME = gobe

# dir and main
DOCS_DIR = ./docs
MAIN = ./cmd/server/main/main.go
DI_DIR = ./internal/di

# default build if not args in make
all: build

# Install and generate swag
swag_install:
	@echo "Installing swag..."
	@go install github.com/swaggo/swag/cmd/swag@latest

# gen docs
# default root ./docs
# custom: --output
# --generalInfo specifics main file
# @swag init --generalInfo $(MAIN) --output ./resources/swagger
swag_gen:
	@echo "Generating swag.."
	@swag init -g $(MAIN)

# Install DI
di_install:
	@echo "Installing wire..."
	@go install github.com/google/wire/cmd/wire@latest

di_gen:
	@echo "Generating wire..."
	@cd $(DI_DIR) && wire gen

# Build the application
build: 
	@echo "Building the application..."
	@go build -v -o $(APP_NAME) $(MAIN)

# run the application
run: 
	@echo "Running the application..."
	@go run $(MAIN)
