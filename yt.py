import streamlit as st
from dotenv import load_dotenv
from youtube_transcript_api import YouTubeTranscriptApi, TranscriptsDisabled, NoTranscriptFound
import requests
import os
import google.generativeai as genai

# Load environment variables
load_dotenv()

# Configure Google Generative AI with your API key
# genai.configure(api_key='AIzaSyDEGqfpIgC2ACm28yQ0uRk8eSkvLPnQmx4')
genai.configure(api_key=os.getenv("GENAI_API_KEY"))

# # RapidAPI credentials
# rapidapi_key = "7e41043a1fmsh27ea57967dcbc9ap1bc07djsnc5a96cb6f9b6"
rapidapi_key = os.getenv("RAPIDAPI_KEY")

rapidapi_host = "youtube-v31.p.rapidapi.com"

# Prompt template for the summarization
prompt = """You are a YouTube video summarizer. You will summarize the content using the following information:
Transcript or video metadata (title, description, etc.). The summary should be concise and under 250 words."""

## Function to extract YouTube video transcript
def extract_transcript_details(video_id):
    try:
        transcript_text = YouTubeTranscriptApi.get_transcript(video_id)
        transcript = ""
        for i in transcript_text:
            transcript += " " + i["text"]
        return transcript

    except TranscriptsDisabled:
        st.warning("Transcripts are disabled for this video.")
        return None

    except NoTranscriptFound:
        st.warning("No transcript found for this video.")
        return None

    except Exception as e:
        st.error(f"An error occurred: {str(e)}")
        return None

## Function to fetch YouTube video metadata using RapidAPI
def fetch_video_metadata(video_id):
    url = "https://youtube-v31.p.rapidapi.com/videos"
    querystring = {"part": "snippet", "id": video_id}
    headers = {
        "x-rapidapi-key": rapidapi_key,
        "x-rapidapi-host": rapidapi_host
    }
    
    response = requests.get(url, headers=headers, params=querystring)
    
    if response.status_code == 200:
        data = response.json()
        if "items" in data and len(data["items"]) > 0:
            video_title = data["items"][0]["snippet"]["title"]
            video_description = data["items"][0]["snippet"]["description"]
            return video_title, video_description
    return None, None

## Function to generate summary from Gemini AI
def generate_gemini_content(text, prompt):
    model = genai.GenerativeModel("gemini-pro")
    response = model.generate_content(prompt + text)
    return response.text

# ## Function to extract the video ID from a YouTube URL
# def extract_video_id(youtube_url):
#     if "youtu.be" in youtube_url:
#         return youtube_url.split("/")[-1]
#     elif "youtube.com" in youtube_url:
#         return youtube_url.split("v=")[1].split("&")[0]
#     else:
#         return None

from urllib.parse import urlparse, parse_qs

def extract_video_id(youtube_url):
    # Parse the URL
    parsed_url = urlparse(youtube_url)
    
    # Handle "youtu.be" links
    if "youtu.be" in parsed_url.netloc:
        return parsed_url.path[1:]  # Extract the video ID from the path, removing the leading '/'
    
    # Handle "youtube.com" links
    if "youtube.com" in parsed_url.netloc:
        query_params = parse_qs(parsed_url.query)
        return query_params.get("v", [None])[0]  # Extract the 'v' parameter from query string
    
    return None

# Streamlit app setup
st.title("YouTube Transcript to Detailed Notes Converter")
youtube_link = st.text_input("Enter YouTube Video Link:")

if youtube_link:
    video_id = extract_video_id(youtube_link)
    
    if video_id:
        thumbnail_url = f"http://img.youtube.com/vi/{video_id}/0.jpg"
        st.image(thumbnail_url, use_column_width=True)
    else:
        st.error("Invalid YouTube link provided. Please check and try again.")

if st.button("Get Detailed Notes"):
    if video_id:
        # Step 1: Try to get the transcript
        transcript_text = extract_transcript_details(video_id)

        # Step 2: If transcript is unavailable, fallback to video metadata
        if transcript_text is None:
            st.warning("Transcript not available. Using video title and description for summarization.")
            video_title, video_description = fetch_video_metadata(video_id)
            if video_title and video_description:
                content = f"Title: {video_title}\n\nDescription: {video_description}"
            else:
                st.error("Unable to retrieve video metadata.")
                content = ""
        else:
            content = transcript_text

        # Step 3: Generate summary using Gemini AI
        if content:
            summary = generate_gemini_content(content, prompt)
            st.markdown("## Detailed Notes:")
            st.write(summary)
    else:
        st.error("Please provide a valid YouTube video link.")

