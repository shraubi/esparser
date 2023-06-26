# Create a new Lambda function in your AWS account. python

aws ecr create-repository --repository-name uparser

# Log in to ECR
aws ecr get-login-password --region eu-central-1 | docker login --username AWS --password-stdin 345731044837.dkr.ecr.eu-central-1.amazonaws.com/uparser

# Build and tag the Docker image
docker build -t uparser:latest .

# Tag the Docker image for ECR
docker tag uparser:latest 345731044837.dkr.ecr.eu-central-1.amazonaws.com/uparser

# Push the Docker image to ECR
docker push 345731044837.dkr.ecr.eu-central-1.amazonaws.com/uparser


# Create Lambda function
<!-- aws lambda publish-layer-version --layer-name my-layer --zip-file fileb://my-layer.zip --compatible-runtimes python3.8
aws lambda invoke --function-name my-function --payload '{}' output.json -->

# Configure a rule in CloudWatch Events to trigger your Lambda function.

docker build -t uparser:latest . && docker tag uparser:latest 345731044837.dkr.ecr.eu-central-1.amazonaws.com/uparser && docker push 345731044837.dkr.ecr.eu-central-1.amazonaws.com/uparser

# Get all the needed variables
export $(cat .env | xargs)

# Start the container like this to avoid breaks after reboot
docker run -d --restart unless-stopped uparser:latest