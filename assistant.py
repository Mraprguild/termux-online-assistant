#!/usr/bin/env python3
# Copyright (c) 2026 Mraprguild
# Licensed under the MIT License
import datetime
import os
import platform
import subprocess
from urllib.parse import quote, quote_plus

import requests

ASSISTANT_NAME = "Mraprguild Online Assistant"
USER_NAME = "Sathish"

HEADERS = {
    "User-Agent": "Mraprguild-Termux-Assistant/1.0 (https://github.com/Mraprguild)"
}

GREEN = "\033[92m"
CYAN = "\033[96m"
WHITE = "\033[97m"
YELLOW = "\033[93m"
RED = "\033[91m"
RESET = "\033[0m"
BOLD = "\033[1m"


def assistant_print(message: str) -> None:
    print(f"\n{CYAN}🤖 {ASSISTANT_NAME}:{RESET}\n{WHITE}{message}{RESET}\n")


def open_url(url: str) -> None:
    try:
        subprocess.run(
            ["termux-open-url", url],
            check=False,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        )
    except FileNotFoundError:
        assistant_print(f"Open this URL manually:\n{url}")


def duckduckgo_answer(question: str):
    endpoint = "https://api.duckduckgo.com/"
    params = {
        "q": question,
        "format": "json",
        "no_html": "1",
        "no_redirect": "1",
        "skip_disambig": "1",
    }

    try:
        response = requests.get(endpoint, params=params, headers=HEADERS, timeout=15)
        response.raise_for_status()
        data = response.json()

        answer = data.get("Answer") or data.get("AbstractText") or data.get("Definition")
        source = data.get("AbstractURL") or data.get("DefinitionURL") or data.get("Redirect")
        source_name = data.get("AbstractSource") or data.get("DefinitionSource") or "DuckDuckGo"

        if answer:
            return {
                "answer": answer.strip(),
                "source": source,
                "source_name": source_name,
            }

        for topic in data.get("RelatedTopics", []):
            if not isinstance(topic, dict):
                continue
            if topic.get("Text"):
                return {
                    "answer": topic["Text"].strip(),
                    "source": topic.get("FirstURL"),
                    "source_name": "DuckDuckGo",
                }
            for nested in topic.get("Topics", []):
                if nested.get("Text"):
                    return {
                        "answer": nested["Text"].strip(),
                        "source": nested.get("FirstURL"),
                        "source_name": "DuckDuckGo",
                    }
    except (requests.RequestException, ValueError):
        return None

    return None


def wikipedia_answer(question: str):
    search_endpoint = "https://en.wikipedia.org/w/api.php"
    search_params = {
        "action": "query",
        "list": "search",
        "srsearch": question,
        "utf8": "1",
        "format": "json",
        "srlimit": "1",
    }

    try:
        search_response = requests.get(
            search_endpoint,
            params=search_params,
            headers=HEADERS,
            timeout=15,
        )
        search_response.raise_for_status()
        results = search_response.json().get("query", {}).get("search", [])

        if not results:
            return None

        title = results[0]["title"]
        summary_url = (
            "https://en.wikipedia.org/api/rest_v1/page/summary/"
            + quote(title, safe="")
        )
        summary_response = requests.get(summary_url, headers=HEADERS, timeout=15)
        summary_response.raise_for_status()
        data = summary_response.json()

        summary = data.get("extract")
        if not summary:
            return None

        page_url = (
            data.get("content_urls", {})
            .get("desktop", {})
            .get("page")
        )

        return {
            "answer": summary.strip(),
            "source": page_url,
            "source_name": "Wikipedia",
        }
    except (requests.RequestException, KeyError, ValueError):
        return None


def online_answer(question: str) -> None:
    question = question.strip()

    if not question:
        assistant_print("Enter a question.")
        return

    print(f"{YELLOW}Searching online...{RESET}")
    result = duckduckgo_answer(question) or wikipedia_answer(question)

    if result:
        output = result["answer"]
        if result.get("source"):
            output += (
                f"\n\n{GREEN}Source: {result['source_name']}{RESET}"
                f"\n{GREEN}{result['source']}{RESET}"
            )
        assistant_print(output)
        return

    search_url = "https://www.google.com/search?q=" + quote_plus(question)
    assistant_print(
        "No direct answer was found.\n\n"
        f"Search results:\n{search_url}"
    )


def show_help() -> None:
    assistant_print(
        """Available commands

ask <question>       Get an online answer
wiki <topic>         Search Wikipedia
search <text>        Open a Google search
open <URL>           Open a website
time                 Show current time
date                 Show current date
device               Show device information
battery              Show battery information
storage              Show storage information
clear                Clear the screen
help                 Display commands
exit                 Close the assistant"""
    )


def show_wikipedia(topic: str) -> None:
    result = wikipedia_answer(topic)
    if not result:
        assistant_print("No Wikipedia article was found.")
        return

    assistant_print(
        f"{result['answer']}\n\n"
        f"{GREEN}Source: Wikipedia{RESET}\n"
        f"{GREEN}{result['source']}{RESET}"
    )


def device_information() -> None:
    assistant_print(
        f"System: {platform.system()}\n"
        f"Machine: {platform.machine()}\n"
        f"Python: {platform.python_version()}\n"
        f"Hostname: {platform.node()}"
    )


def battery_information() -> None:
    try:
        result = subprocess.run(
            ["termux-battery-status"],
            capture_output=True,
            text=True,
            timeout=10,
            check=False,
        )
        if result.returncode == 0:
            assistant_print(result.stdout.strip())
        else:
            assistant_print("Install Termux API support:\npkg install termux-api -y")
    except (FileNotFoundError, subprocess.TimeoutExpired):
        assistant_print("Install Termux API support:\npkg install termux-api -y")


def process_command(command: str) -> bool:
    command = command.strip()
    lower = command.lower()

    if not command:
        return True

    if lower in {"exit", "quit", "bye"}:
        assistant_print(f"Goodbye, {USER_NAME}!")
        return False
    if lower in {"help", "commands"}:
        show_help()
    elif lower.startswith("ask "):
        online_answer(command[4:])
    elif lower.startswith("wiki "):
        show_wikipedia(command[5:].strip())
    elif lower.startswith("search "):
        query = command[7:].strip()
        if query:
            open_url("https://www.google.com/search?q=" + quote_plus(query))
        else:
            assistant_print("Enter something to search.")
    elif lower.startswith("open "):
        url = command[5:].strip()
        if not url.startswith(("https://", "http://")):
            url = "https://" + url
        open_url(url)
    elif lower == "time":
        assistant_print(datetime.datetime.now().strftime("Current time: %I:%M:%S %p"))
    elif lower == "date":
        assistant_print(datetime.datetime.now().strftime("Today: %A, %d %B %Y"))
    elif lower == "device":
        device_information()
    elif lower == "battery":
        battery_information()
    elif lower == "storage":
        os.system("df -h")
    elif lower == "clear":
        os.system("clear")
    elif lower in {"hello", "hi", "hey"}:
        assistant_print(f"Hello {USER_NAME}! Ask me an online question.")
    else:
        online_answer(command)

    return True


def main() -> None:
    os.system("clear")
    print(
        f"""{CYAN}
╔══════════════════════════════════════════╗
║      {GREEN}MRAPRGUILD ONLINE ASSISTANT{CYAN}         ║
║         Termux Text Edition              ║
╠══════════════════════════════════════════╣
║  Online answers • Sources • Wikipedia    ║
╚══════════════════════════════════════════╝
{RESET}"""
    )
    assistant_print(f"Welcome, {USER_NAME}!\nEnter a question or type help.")

    while True:
        try:
            command = input(f"{GREEN}👤 {USER_NAME}:{RESET} ")
            if not process_command(command):
                break
        except KeyboardInterrupt:
            print()
            assistant_print("Type exit to close the assistant.")
        except EOFError:
            assistant_print("Goodbye!")
            break
        except Exception as error:
            assistant_print(f"Unexpected error: {error}")


if __name__ == "__main__":
    main()
