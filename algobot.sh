#!/bin/bash
# AlgoBot Development Script
# This script provides commands for local development and deployment

# Define colors for console output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Display header
echo -e "${BLUE}===================================${NC}"
echo -e "${BLUE}    AlgoBot Development Script     ${NC}"
echo -e "${BLUE}===================================${NC}"

# Function to display help menu
show_help() {
    echo -e "${BLUE}Available commands:${NC}"
    echo -e "  ${GREEN}start${NC}       - Start all services in development mode"
    echo -e "  ${GREEN}build${NC}       - Build Docker images"
    echo -e "  ${GREEN}deploy${NC}      - Deploy to production"
    echo -e "  ${GREEN}test${NC}        - Run all tests"
    echo -e "  ${GREEN}test:backend${NC} - Run backend tests"
    echo -e "  ${GREEN}test:frontend${NC} - Run frontend tests"
    echo -e "  ${GREEN}clean${NC}       - Remove all containers and volumes"
    echo -e "  ${GREEN}logs${NC}        - Follow container logs"
    echo -e "  ${GREEN}help${NC}        - Show this help message"
}

# Function to start development environment
start_dev() {
    echo -e "${YELLOW}Starting all services in development mode...${NC}"
    docker-compose up -d
    echo -e "${GREEN}Services started! Access:${NC}"
    echo -e "  ${BLUE}Frontend:${NC} http://localhost:3000"
    echo -e "  ${BLUE}Backend API:${NC} http://localhost:8000"
    echo -e "  ${BLUE}API Docs:${NC} http://localhost:8000/docs"
}

# Function to build Docker images
build_images() {
    echo -e "${YELLOW}Building Docker images...${NC}"
    docker-compose build
    echo -e "${GREEN}Docker images built successfully!${NC}"
}

# Function to deploy to production
deploy_prod() {
    echo -e "${YELLOW}Deploying to production...${NC}"
    
    # Check if .env.prod exists
    if [ ! -f .env.prod ]; then
        echo -e "${RED}Error: .env.prod file not found!${NC}"
        echo -e "Please create a .env.prod file with your production environment variables."
        exit 1
    fi
    
    # Run tests before deploying
    echo -e "${BLUE}Running tests before deployment...${NC}"
    run_tests
    
    if [ $? -ne 0 ]; then
        echo -e "${RED}Tests failed! Deployment aborted.${NC}"
        exit 1
    fi
    
    echo -e "${BLUE}Tests passed! Continuing with deployment...${NC}"
    docker-compose -f docker-compose.prod.yml --env-file .env.prod up -d
    
    echo -e "${GREEN}Deployment completed successfully!${NC}"
}

# Function to run all tests
run_tests() {
    echo -e "${YELLOW}Running all tests...${NC}"
    run_backend_tests
    run_frontend_tests
}

# Function to run backend tests
run_backend_tests() {
    echo -e "${YELLOW}Running backend tests...${NC}"
    docker-compose run --rm backend pytest
}

# Function to run frontend tests
run_frontend_tests() {
    echo -e "${YELLOW}Running frontend tests...${NC}"
    docker-compose run --rm frontend npm test
}

# Function to clean up all containers and volumes
clean_env() {
    echo -e "${YELLOW}Cleaning up Docker resources...${NC}"
    docker-compose down -v
    echo -e "${GREEN}Cleanup completed!${NC}"
}

# Function to follow container logs
follow_logs() {
    echo -e "${YELLOW}Following container logs... (Ctrl+C to exit)${NC}"
    docker-compose logs -f
}

# Parse command line arguments
case "$1" in
    start)
        start_dev
        ;;
    build)
        build_images
        ;;
    deploy)
        deploy_prod
        ;;
    test)
        run_tests
        ;;
    test:backend)
        run_backend_tests
        ;;
    test:frontend)
        run_frontend_tests
        ;;
    clean)
        clean_env
        ;;
    logs)
        follow_logs
        ;;
    help|*)
        show_help
        ;;
esac

exit 0
