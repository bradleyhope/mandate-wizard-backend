> # Mandate Wizard V5.0.0 - Release Notes
> 
> **Release Date:** October 24, 2025

---

## 🎉 New Feature: High-Performance Streaming Responses

Version 5.0.0 introduces a major architectural upgrade, replacing the traditional request-response model with a high-performance streaming backend powered by Server-Sent Events (SSE). This enhancement was driven by the need to support complex, long-running queries (often exceeding 30 seconds) without causing request timeouts or leaving the user waiting for a response.

### Key Benefits

-   **Seamless User Experience:** Answers now stream to the user in real-time, providing immediate feedback and a more interactive, conversational feel.
-   **No More Timeouts:** The streaming architecture eliminates the risk of request timeouts for long-running queries, ensuring that even the most complex questions are answered successfully.
-   **Real-time Progress Updates:** The user is kept informed of the query processing status with real-time updates, such as "Classifying intent..." and "Searching graph database...".

## Bug Fixes and Improvements

-   **`None.lower()` Error:** Fixed a critical bug where the application would crash if a Neo4j record had a `null` value for `current_title`. The system now gracefully handles null values.
-   **OpenAI API Authentication:** Resolved an issue where the application was using an expired sandbox token. The OpenAI client initialization has been updated to correctly handle different API keys and base URLs.
-   **Model Name Correction:** Updated the language model from the non-existent "gpt-5" to the correct "gpt-4o" model, resolving long response times and timeouts.

## Testing and Validation

-   **100% Pass Rate:** V5 has successfully passed a comprehensive testing framework covering 12 distinct user personas, with a 100% success rate.
-   **Performance:** Average response time is **4.80 seconds**, well under the 30+ second threshold that this version was built to address.
-   **Feature Validation:** All key features, including intent classification, regional/format routing, and Task 1A/1B data integration (quotes and projects), have been verified as fully functional.

## Documentation

-   **README.md:** Updated with details on the new streaming architecture, setup instructions, and testing procedures.
-   **DEPLOYMENT.md:** A new guide providing detailed instructions for deploying the application to a production environment using Gunicorn, Docker, or cloud platforms.

---

*Mandate Wizard V5 is now faster, more robust, and provides a significantly improved user experience. Thank you for your continued support!*
