import os
from apify_client import ApifyClient


import openai
from flask import Flask, redirect, render_template, request, url_for

app = Flask(__name__)
openai.api_key =""


@app.route("/", methods=("GET", "POST"))
def index():
    if request.method == "GET":
        loading = False
    #function to get today's date
    def get_date():
        from datetime import date
        today = date.today()
        return today.strftime("%Y-%m-%d")
    if request.method == "POST":
        response = request.form.get("response")
        loading = True
        rubric = request.form["rubric"]
        publication = request.form.get("publication")
        language = request.form.get("language")
        #set articleURL to the text input in the form called url
        articleURL = request.form["url"]

        client = ApifyClient("apify_api_lzHUIuI1Y5HEK647mVFYBOPY2Wrumj0Exkoh")
        if(articleURL != ""):
            #verify that the url is a valid article
            if(articleURL.find("https://www.") == -1):
                #render "invalid url" in the text box
                loading = False
                return redirect(url_for("index", result="Please enter a valid URL.", loading=loading))

            run_input = {
                "articleUrls": [{ "url": articleURL}],
                "isUrlArticleDefinition": {
                    "minDashes": 4,
                    "hasDate": True,
                    "linkIncludes": [
                        "article",
                        "storyid",
                        "?p=",
                        "id=",
                        "/fpss/track",
                        ".html",
                        "/content/",
                    ],
                },
                "proxyConfiguration": { "useApifyProxy": True },
                "maxArticlesPerCrawl": 1,
                "extendOutputFunction": """($) => {
                const result = {};
                // Uncomment to add a title to the output
                // result.pageTitle = $('title').text().trim();

                return result;
            }""",
            }

            # Run the actor and wait for it to finish
            run = client.actor("lukaskrivka/article-extractor-smart").call(run_input=run_input)

            for item in client.dataset(run["defaultDatasetId"]).iterate_items():
                # Print the article title
                # Use the OpenAI GPT API to generate a summary of the articleen briefly explain
                prompt = f"Translate the text that follows to {language}. Summarize the key points of this text in 10 sentences in {language}, first giving background on the situation and what's currently happening in {language}, thing the article in {language}. {rubric} Paraphrase and rewrite sentences in {language}, instead of copying them verbatim. End the summary with a joke and something important which may happen soon regarding the story. :                                                          Article Title:{item['title']}\n {item['text']}"
                response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=300, temperature=0.9, top_p=1, frequency_penalty=0, presence_penalty=0.6)
                summary = item['title'] + ' ' + item['url'] + '\n'+ response["choices"][0]["text"]
                loading = False
            return redirect(url_for("index", result=summary, loading=loading))
        if(publication == "nytimes"):
            url = "https://www.nytimes.com/" + response
        elif(publication == "bbc"):
            url = "https://www.bbc.com/" + response
        elif(publication == "fox"):
            url = "https://www.foxnews.com/"
        elif(publication == "cnn"):
            url = "https://www.cnn.com/" + response
        elif(publication == "washingtonpost"):
            url = "https://www.washingtonpost.com/" 
            if(response != "arts"):
                url += response
        elif(publication == "npr"):
            url = "https://www.npr.org/" + response
        
        #include "section/ + topic + /" in the url

        run_input = {
            "startUrls": [{ "url": url }],
            "isUrlArticleDefinition": {
                "minDashes": 4,
                "hasDate": True,
                "linkIncludes": [
                    "article",
                    "storyid",
                    "?p=",
                    "id=",
                    "/fpss/track",
                    ".html",
                    "/content/",
                ],
            },
            "proxyConfiguration": { "useApifyProxy": True },
            "maxArticlesPerCrawl": 1,
            "dateFrom": get_date(),
            "extendOutputFunction": """($) => {
            const result = {};
            // Uncomment to add a title to the output
            // result.pageTitle = $('title').text().trim();

            return result;
        }""",
        }

        # Run the actor and wait for it to finish
        run = client.actor("lukaskrivka/article-extractor-smart").call(run_input=run_input)

        for item in client.dataset(run["defaultDatasetId"]).iterate_items():
            # Print the article title
            # Use the OpenAI GPT API to generate a summary of the article
            prompt = f"Summarize the key points of this text in {language}, first giving background on the situation and what's currently happening, then briefly explaining the article. {rubric} Paraphrase and rewrite sentences in {language}, instead of copying them verbatim. End the summary with a joke and something important which may happen soon regarding the story. :                                                          Article Title:{item['title']}\n {item['text']}"
            response = openai.Completion.create(engine="text-davinci-002", prompt=prompt, max_tokens=300, temperature=0.5, top_p=1, frequency_penalty=0, presence_penalty=0.6)
            summary = item['title'] + ' ' + item['url'] + '\n'+ response["choices"][0]["text"]
            loading = False
        return redirect(url_for("index", result=summary, loading=loading))

    result = request.args.get("result")
    loading = False
    return render_template("index.html", loading=loading, result=result)
