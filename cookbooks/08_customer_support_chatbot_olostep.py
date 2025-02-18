# QuickBlox's Customer Support Chatbot with Olostep!
# This cookbook demonstrates how to build an efficient customer support chatbot.
# Along with combining Olostep's superior web scraping capabilities with Julep's Agentic features.

# Step 0: Setup and Configuration
# -----------------------------

# Required Environment Variables:
# - JULEP_API_KEY: Your Julep API key
# - OLOSTEP_API_KEY: Your Olostep API key

import os

# Set API keys before imports

from dotenv import load_dotenv
import requests
import time
import json
from julep import Client
from concurrent.futures import ThreadPoolExecutor, as_completed

# Initialize Julep client with development environment

client = Client(api_key=os.environ["JULEP_API_KEY"], environment="dev")

# Use existing agent ID - this agent is already set up for processing Quickblox content

AGENT_UUID = "464a2c3e-7413-44de-8c91-5a91b1dbfafa"

# Step 1: Define the Olostep Scraper
# --------------------------------
# Olostep provides superior web scraping capabilities:
# - 1-6 second response time (vs. traditional crawlers)
# - Built-in bot detection avoidance
# - Handles JavaScript-rendered content
# - Clean content extraction with transformers

class AdvancedScraper:
    """Enhanced web scraper using Olostep's API"""
    
    def __init__(self, api_key):
        self.headers = {
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json"
        }
        self.base_url = "https://api.olostep.com/v1"

    def scrape_single_page(self, url):
        """
        Easily Scrape a single page with advanced features
        
        Args:
            url (str): The URL to scrape
            
        Returns:
            dict: Contains scraped content and metadata, or None if scraping failed
        """
        print(f"\nScraping {url}...")
        
        # Configure scraping parameters for optimal results
        
        payload = {
            "url_to_scrape": url,
            "formats": ["markdown"],              # Get clean markdown content
            "transformer": "postlight",           # Use Postlight parser for better extraction
            "remove_css_selectors": "default",    # Remove unnecessary elements
            "screen_size": {
                "screen_type": "desktop"          # Use desktop view for consistent results
            }
        }

        try:
            
            # Execute scraping request
            
            response = requests.post(
                f"{self.base_url}/scrapes",
                json=payload,
                headers=self.headers
            )
            response.raise_for_status()
            
            result = response.json()
            print(f"Successfully scraped {url}")
            
            # Extract and return clean content
            
            if result and result.get('result', {}).get('markdown_content'):
                return {
                    'url': url,
                    'content': result['result']['markdown_content']
                }
            return None

        except Exception as e:
            print(f"Error scraping {url}: {str(e)}")
            return None

# Step 2: Define Target URLs
# ------------------------
# These URLs will be scraped to build the knowledge base

urls_to_scrape = [
    "https://quickblox.com/",           # Main product information
    "https://quickblox.com/pricing/",   # Pricing details
    "https://quickblox.com/features/",  # Feature specifications
]

def main():
    """
    Main execution flow:
    1. Scrape content using Olostep (in parallel)
    2. Process and store content in Julep
    3. Create chat interface
    4. Test with sample questions
    """
    
    # Initialize Olostep scraper
    
    scraper = AdvancedScraper(os.environ["OLOSTEP_API_KEY"])
    
    print("Starting parallel scraping process...")
    
    # Step 3: Gather Content (Parallel Scraping)
    # ----------------------------------------
    
    all_results = []
    with ThreadPoolExecutor(max_workers=3) as executor:
        # Submit all scraping tasks
        future_to_url = {
            executor.submit(scraper.scrape_single_page, url): url 
            for url in urls_to_scrape
        }
        
        # Process results as they complete
        for future in as_completed(future_to_url):
            url = future_to_url[future]
            try:
                result = future.result()
                if result:
                    all_results.append(result)
                    print(f"✅ Completed: {url}")
            except Exception as e:
                print(f"❌ Failed: {url} - {str(e)}")
    
    print(f"\nCompleted scraping {len(all_results)}/{len(urls_to_scrape)} URLs")
    
    # Save raw results for reference
    
    with open("scrape_results.json", "w") as f:
        json.dump(all_results, f, indent=2)
    print("\nRaw results saved to scrape_results.json")
    
    # Step 4: Process Content into Julep
    # --------------------------------
    
    print("\nProcessing results into Julep documents...")
    for result in all_results:
        if result and result.get('content'):
            doc_title = f"Quickblox - {result['url']}"
            print(f"Creating document: {doc_title}")
            
            # Create document with metadata
            client.agents.docs.create(
                agent_id=AGENT_UUID,
                metadata={
                    "source": "olostep",
                    "url": result['url']
                },
                title=doc_title,
                content=result['content']
            )
    
    # Step 5: Create Chat Interface
    # ---------------------------
    
    print("\nCreating chat session...")
    session = client.sessions.create(
        agent=AGENT_UUID,
        situation="""
        You are an AI assistant that helps users understand Quickblox's products and services.
        Use the provided documentation to answer questions accurately.
        """,
        recall_options={
            "mode": "hybrid",           # Use hybrid search for better recall
            "confidence": 0.7,          # High confidence threshold
            "limit": 10                 # Return top 10 relevant documents
        }
    )
    
    # Step 6: Test the Chatbot
    # -----------------------
    
    print("\nTesting chat...")
    test_questions = [
        "What are Quickblox's main products?",
        "What are the pricing plans?",
        "What platforms are supported?"
    ]
    
    for question in test_questions:
        print(f"\nQ: {question}")
        response = client.sessions.chat(
            session_id=session.id,
            messages=[{
                "role": "user",
                "content": question
            }],
            recall=True
        )
        print("A:", response.choices[0].message.content)

        print(f"\nQ: {question}")
        response = client.sessions.chat(
            session_id=session.id,
            messages=[{
                "role": "user",
                "content": question
            }],
            recall=True
        )
        print("A:", response.choices[0].message.content)

if __name__ == "__main__":
    main()
 
 
# OUTPUT IS AS FOLLOWS -->

# Starting parallel scraping process...

# Scraping https://quickblox.com/...
# Scraping https://quickblox.com/pricing/...
# Scraping https://quickblox.com/features/...

# Successfully scraped https://quickblox.com/
# ✅ Completed: https://quickblox.com/

# Successfully scraped https://quickblox.com/pricing/
# ✅ Completed: https://quickblox.com/pricing/

# Successfully scraped https://quickblox.com/features/
# ✅ Completed: https://quickblox.com/features/

# Completed scraping 3/3 URLs

# Raw results saved to scrape_results.json

# Processing results into Julep documents...
# Creating document: Quickblox - https://quickblox.com/
# Creating document: Quickblox - https://quickblox.com/pricing/
# Creating document: Quickblox - https://quickblox.com/features/

# Creating chat session...

# Testing chat...

# Q: What are Quickblox's main products?
# A: QuickBlox offers a range of main products grouped under several categories:

# 1. **Communication Tools**:
#    - **SDKs and APIs**: These include reliable and robust tools for adding communication features to any app or website. Specific SDKs available are iOS SDK, Android SDK, JavaScript SDK, React Native SDK, Flutter SDK, and a general Chat API.
#    - **Chat UI Kits**: Pre-built UI components that enable developers to build their own messenger app efficiently. These kits are aimed at easing the process of UI design for messaging applications.

# 2. **QuickBlox AI**:
#    - **SmartChat Assistant**: This is an AI-powered in-app virtual assistant trained on your own data to help improve user interaction within the app.
#    - **AI Extensions**: These are AI features that can be integrated into any chat app to enhance its functionality with AI capabilities.

# 3. **White Label Solutions**:
#    - **Q-Consultation**: A white-label solution offering video calling with virtual meeting rooms and in-app chat, tailored to businesses that need a virtual consultation capability.
#    - **Q-Municate**: A customizable messaging app that supports secure chat, aimed at businesses that want to build or integrate a messaging system under their own branding.

# These products are designed to enhance communication and engagement across various industries, ensuring businesses can deploy advanced messaging, video calling, and AI interaction tools without extensive development time.

# Q: What are Quickblox's main products?
# A: QuickBlox offers a range of products primarily focused on communication tools, which are grouped into several key categories:

# 1. **Communication Tools:**
#    - **SDKs and APIs**: These are reliable and robust software tools that enable the integration of communication features into any app or website. Specific SDKs offered include:
#      - iOS SDK
#      - Android SDK
#      - JavaScript SDK
#      - React Native SDK
#      - Flutter SDK
#    - **Chat API**: A comprehensive API that facilitates the building of chat functionality into applications.
#    - **Chat UI Kits**: These UI kits are pre-built user interface components designed to help developers quickly build their own messenger apps across various platforms.

# 2. **QuickBlox AI:**
#    - **SmartChat Assistant**: These are in-app virtual assistants that are trained on your data to provide support and interaction capabilities within applications.  
#    - **AI Extensions**: Additional AI-driven features that can be incorporated into chat applications to enhance functionality and user engagement.

# 3. **White Label Solutions:**
#    - **Q-Consultation**: A white-label solution for video calling that includes virtual meeting rooms and in-app chat functionality, tailored for sectors like healthcare and consulting.
#    - **Q-Municate**: A customizable and secure messaging app solution that can be tailored to fit the branding and specific needs of a business.

# These products are designed to enhance digital communication across various industries, providing tools for chat, video calling, and artificial intelligence interactions.

# Q: What are the pricing plans?
# A: QuickBlox offers various pricing plans tailored to different sizes and types of businesses, including a free option. Here are the details of the plans offered:

# 1. **Basic Plan**:
#    - **Price**: Free
#    - **Total Users**: 500 users
#    - **Data Retention**: 1 month
#    - **File Size Limit**: 10 MB
#    - **Core Features**: Includes native and cross-platform SDKs, 1-1 chat, group chat, chat history, and more.
#    - **Advanced Features**: Lacks certain capabilities such as custom classes, sync across multiple devices, etc.
#    - **Peer-to-peer audio/video calls**: Included
#    - **Conference audio/video calls**: Available as an add-on

# 2. **Starter Plan**:
#    - **Price**: $107 per month
#    - **Total Users**: 10,000 users
#    - **Data Retention**: 3 months
#    - **File Size Limit**: 25 MB
#    - **Core and Advanced Features**: Full access to all core features plus advanced features such as custom classes, sync across devices, server API, etc.
#    - **Peer-to-peer and conference audio/video calls**: Included
#    - **AI Extensions**: 2 extensions
#    - **SmartChat Assistant**: 1 bot

# 3. **Growth Plan**:
#    - **Price**: $269 per month
#    - **Total Users**: 25,000 users
#    - **Data Retention**: 6 months
#    - **File Size Limit**: 50 MB
#    - **Core and Advanced Features**: All included.
#    - **Peer-to-peer and conference audio/video calls**: Included
#    - **AI Extensions**: 3 extensions
#    - **SmartChat Assistant**: 2 bots

# 4. **HIPAA Cloud Plan**:
#    - **Price**: $430 per month
#    - **Total Users**: 20,000 users
#    - **Data Retention**: Custom
#    - **File Size Limit**: 50 MB
#    - **Core and Advanced Features**: All included, along with HIPAA compliance.
#    - **Peer-to-peer and conference audio/video calls**: Included
#    - **Data Encryption**: Included
#    - **SmartChat Assistant**: 2 bots

# 5. **Enterprise Plan**:
#    - **Price**: Starts from $647, varies as customizable to specific business needs.
#    - **Total Users**: Custom
#    - **Data Retention**: Custom
#    - **File Size Limit**: Custom
#    - **Core and Advanced Features**: All included; fully customizable.
#    - **AI Extensions**: All 5 extensions
#    - **SmartChat Assistant**: 3 bots; additional bots purchasable
#    - **Dedicated Server**: Available

# These plans are designed to cater from small startup needs to large enterprise requirements, including options for businesses needing HIPAA-compliant solutions. Additional details and potential discounts for more extensive usage or longer commitment periods can generally be negotiated with QuickBlox's sales team.

# Q: What are the pricing plans?
# A: QuickBlox offers various pricing plans designed for businesses of different sizes and needs, ranging from a basic free plan to advanced enterprise solutions. Here’s an overview of their current pricing structure:

# ### 1. Basic Plan
#    - **Price**: Free
#    - **Total Users**: 500
#    - **Data Retention**: 1 month
#    - **File Size Limit**: 10 MB
#    - **Core Features**: Includes native and cross-platform SDKs, 1-1 chat, group chat, and more.
#    - **Advanced Features**: Not included (e.g., Custom classes, Offline Messages, etc.)
#    - **AI Extensions**: 1 extension
#    - **SmartChat Assistant**: Available with a 30-day free trial on the bot

# ### 2. Starter Plan
#    - **Price**: $107 per month
#    - **Total Users**: 10,000
#    - **Data Retention**: 3 months
#    - **File Size Limit**: 25 MB
#    - **Core Features**: Includes all basic features plus advanced features like sync across multiple devices, server API, etc.
#    - **AI Extensions**: 2 extensions
#    - **SmartChat Assistant**: 1 bot
#    - **Support**: Ticketing system

# ### 3. Growth Plan
#    - **Price**: $269 per month
#    - **Total Users**: 25,000
#    - **Data Retention**: 6 months
#    - **File Size Limit**: 50 MB
#    - **AI Extensions**: 3 extensions
#    - **SmartChat Assistant**: 2 bots
#    - **Support**: Ticketing system

# ### 4. HIPAA Cloud Plan
#    - **Price**: $430 per month
#    - **Total Users**: 20,000
#    - **Data Retention**: Custom
#    - **File Size Limit**: 50 MB
#    - **Core and Advanced Features**: All included, HIPAA compliant
#    - **AI Extensions**: 3 extensions
#    - **SmartChat Assistant**: 2 bots
#    - **Support**: Ticketing system

# ### 5. Enterprise Plan
#    - **Price**: From $647 (customizable based on the specific requirements)
#    - **Total Users**: Custom
#    - **Data Retention**: Custom
#    - **File Size Limit**: Custom
#    - **Core and Advanced Features**: All included; fully customizable.
#    - **AI Extensions**: All 5 extensions
#    - **SmartChat Assistant**: 3 or more bots (additional bots can be purchased)
#    - **Support**: SLA, Account manager, Ticketing system

# These plans include a range of features suited for startups, growth-phase companies, and large enterprises needing custom solutions or HIPAA-compliant services.      

# Q: What platforms are supported?
# A: QuickBlox provides comprehensive support across multiple platforms to ensure developers can integrate chat and communication features into applications no matter what environment they are working with. Here are the platforms for which QuickBlox offers dedicated SDKs:

# 1. **iOS**: The iOS SDK allows developers to integrate messaging, voice, and video calling features into any iOS application efficiently.

# 2. **Android**: The Android SDK supports adding real-time chat, voice, and video functionalities to Android apps.

# 3. **JavaScript**: QuickBlox's JavaScript SDK can be used to integrate communication tools into any web applications, enhancing the interactivity of websites.        

# 4. **React Native**: This SDK is specially designed for cross-platform mobile apps, allowing the same codebase to work on both iOS and Android platforms using React Native.

# 5. **Flutter**: With the Flutter SDK, developers can build natively compiled applications for mobile, web, and desktop from a single codebase.

# These SDKs ensure that QuickBlox services are accessible across the most widely used platforms, giving developers the flexibility to build or enhance their applications with robust communication tools across different devices and operating systems.

# Q: What platforms are supported?
# A: QuickBlox provides support across multiple platforms by offering specialized SDKs (Software Development Kits) and APIs (Application Programming Interfaces) for each. Here are the platforms supported by QuickBlox:

# 1. **iOS**: The iOS SDK allows you to integrate chat, voice, and video calling features into any iOS application.

# 2. **Android**: The Android SDK supports adding comprehensive communication features into Android apps.

# 3. **JavaScript**: The JavaScript SDK is designed for web applications, enabling real-time communication capabilities within browsers.

# 4. **React Native**: This SDK enables developers to build cross-platform apps for iOS and Android using React Native, integrating chat and communication features seamlessly.

# 5. **Flutter**: The Flutter SDK supports the creation of natively compiled applications for mobile, web, and desktop from a single codebase, incorporating robust chat and communication functionalities.

# These SDKs ensure that developers can leverage QuickBlox's communication tools across different environments, making it versatile for integrating into various application ecosystems.