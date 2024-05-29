
## A&D Coiffure du monde

### The best hair salon for braids

Welcome to A&D Coiffure du Monde, your one-stop shop for all your haircare needs! 
We are a team of licensed stylists based in Gaithersburg, MD, passionate about 
helping you achieve your hair goals and cultivate healthy, beautiful hair.


### The Technical Stuff 

Languages: 
> ### Web Pages: HTML, CSS and some Javascript
> (You could probably already tell.)

> ### Server: Flask
> Using flask to handle URL routing and serve web pages over hhtp requests.

> ### Other Tools: Nginx and Docker
> Using nginx as a reverse proxy to listen for requests.
> Nginx has also been configured to all incoming requests to https requests.
> Certbot was used to obtain an ssl certificate and install it on the server. 
> The https requests is then routed to the running flask app.
>
> Docker is used to create and start 2 containers. One container holds an image of the flask app.
> The other holds an image of the nginx service. The Docker compose file is configured to add the
> nginx config, and SSL certificate files to the environment of the nginx image. At the moment of
> writing, the flask app is configured to listen for traffic on port 5000(see app.py), while the nginx service
> is configured to listen for traffic on port 443 and route that traffic to port 5000(see nginx.conf).


### Deploying the app 
1. Build the image.

``` docker build -t image_name . ```

2. Save the image in a tar file

``` docker save -o placeholdername.tar image_name ```

3. Send the image to the live server

``` scp -i path/to/key.pem placeholdername.tar user@server_address:/path/to/project/ ```

4. Send the nginx config and docker compose file to the server

``` scp -i path/to/key.pem nginx.conf user@server_address:/path/to/project/ ```

5. Unpack the tar file on the server

``` sudo docker load -i placeholder.tar ```

6. Start the containers with docker compose

``` docker-compose up -d ```



