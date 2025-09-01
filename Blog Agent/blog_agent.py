# blog_agent.py
# 📢 Blog → Quora & Reddit Agent with Streamlit + Playwright
# Author: Sagar's AI Assistant

import streamlit as st
import requests
from bs4 import BeautifulSoup
import asyncio
import json
from playwright.async_api import async_playwright
import openai

# 🔑 Set your API key here (or use environment variable)
openai.api_key = "YOUR_OPENAI_API_KEY"

# -----------------------------
# Summarizers (Quora & Reddit)
# -----------------------------
def summarize_for_quora(content):
    prompt = f"Write a helpful Quora answer based on this blog:\n\n{content}"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=300
    )
    return response.choices[0].text.strip()

def summarize_for_reddit(content):
    prompt = f"Convert this blog into a Reddit discussion post with a title and body:\n\n{content}"
    response = openai.Completion.create(
        engine="gpt-3.5-turbo-instruct",
        prompt=prompt,
        max_tokens=400
    )
    return response.choices[0].text.strip()

# -----------------------------
# Blog Scraper
# -----------------------------
def fetch_blog_content(url):
    try:
        page = requests.get(url, timeout=10)
        soup = BeautifulSoup(page.text, "html.parser")
        paragraphs = [p.get_text() for p in soup.find_all("p")]
        return " ".join(paragraphs[:10])  # first 10 paragraphs
    except Exception as e:
        return f"Error fetching blog: {e}"

# -----------------------------
# Quora Posting
# -----------------------------
async def post_to_quora(question_url, answer_text):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        # Load cookies (saved manually)
        with open("quora_cookies.json") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(question_url)

        # Type answer
        await page.wait_for_selector("div.q-box.qu-mb--tiny")
        await page.click("div.q-box.qu-mb--tiny")
        await page.keyboard.type(answer_text, delay=50)
        await page.click("text=Post")

        await asyncio.sleep(5)
        await browser.close()

# -----------------------------
# Reddit Posting
# -----------------------------
async def post_to_reddit(subreddit, title, body):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=False)
        context = await browser.new_context()

        with open("reddit_cookies.json") as f:
            cookies = json.load(f)
        await context.add_cookies(cookies)

        page = await context.new_page()
        await page.goto(f"https://www.reddit.com/r/{subreddit}/submit")

        await page.fill("textarea[name='title']", title)
        await page.fill("div[role='textbox']", body)
        await page.click("button:has-text('Post')")

        await asyncio.sleep(5)
        await browser.close()

# -----------------------------
# Streamlit UI
# -----------------------------
st.set_page_config(page_title="Blog → Quora & Reddit Agent", page_icon="📢")
st.title("📢 Blog → Quora & Reddit Agent")

blog_url = st.text_input("Enter Blog URL:")
question_url = st.text_input("Quora Question URL (where you want to post):")
subreddit = st.text_input("Reddit Subreddit:")

if st.button("Summarize Blog"):
    if blog_url:
        content = fetch_blog_content(blog_url)

        st.subheader("Extracted Blog Content:")
        st.write(content[:500] + "..." if len(content) > 500 else content)

        quora_text = summarize_for_quora(content)
        reddit_text = summarize_for_reddit(content)

        st.subheader("Quora Answer Preview:")
        st.write(quora_text)

        st.subheader("Reddit Post Preview:")
        st.write(reddit_text)

        # Post buttons
        if st.button("🚀 Post to Quora"):
            asyncio.run(post_to_quora(question_url, quora_text))
            st.success("✅ Posted to Quora!")

        if st.button("🚀 Post to Reddit"):
            reddit_parts = reddit_text.split("\n", 1)
            title, body = reddit_parts[0], reddit_parts[1] if len(reddit_parts) > 1 else ""
            asyncio.run(post_to_reddit(subreddit, title, body))
            st.success("✅ Posted to Reddit!")
    else:
        st.warning("⚠️ Please enter a blog URL.")
