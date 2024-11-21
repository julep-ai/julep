from environs import Env

# Initialize the Env object for environment variable parsing.
env = Env()
env.read_env()  # Read .env file, if it exists

# Load environment variables
rapid_api_key = env.str("RAPID_API_KEY")
rapid_api_host = env.str("RAPID_API_HOST")
aryshare_key = env.str("ARYSHARE_KEY")
aryshare_profile_id = env.str("ARYSHARE_PROFILE_ID")
browserbase_api_key = env.str("BROWSERBASE_API_KEY")
browserbase_project_id = env.str("BROWSERBASE_PROJECT_ID")
openweather_api_key = env.str("OPENWEATHER_API_KEY")
spider_api_key = env.str("SPIDER_API_KEY")
brave_api_key = env.str("BRAVE_API_KEY")
llama_api_key = env.str("LLAMA_API_KEY")
cloudinary_api_key = env.str("CLOUDINARY_API_KEY")
cloudinary_api_secret = env.str("CLOUDINARY_API_SECRET")
cloudinary_cloud_name = env.str("CLOUDINARY_CLOUD_NAME")
mailgun_password = env.str("MAILGUN_PASSWORD")
