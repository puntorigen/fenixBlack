# Step 1: Build the React application
# Use an official Node.js image as the base image
FROM node:16-alpine as builder

# Set the working directory in the Docker container
WORKDIR /web

# Copy the package.json and package-lock.json
COPY package*.json ./
 
# Install dependencies
RUN npm install

# Copy the rest of your app's source code from your host to your image filesystem.
COPY . .

# Build the project (this creates the build directory)
RUN npm run build

EXPOSE 3000

CMD ["npm", "start"]

# Step 2: Serve the app with Nginx (production)
# Use an official Nginx image as the base image for the serving stage
#FROM nginx:alpine

# Copy the built assets from the builder stage
#COPY --from=builder /web/build /usr/share/nginx/html

# Expose port 80 to the outside once the container has launched
#EXPOSE 80

# Start Nginx server
#CMD ["nginx", "-g", "daemon off;"]
