# web/Dockerfile
FROM nginx:alpine

# Copy the HTML file to the nginx HTML directory
COPY ./index.html /usr/share/nginx/html/index.html

# Expose port 80
EXPOSE 80

# Start Nginx server
CMD ["nginx", "-g", "daemon off;"]