# Resilient E-Commerce Data Pipeline (Hepco & Becker Crawler)

`Python` `Selenium` `Data-Pipeline` `Networking` `ETL` `Resilience`

## 1\. Project Overview

This project is a complete, end-to-end **ETL (Extract, Transform, Load) data pipeline** designed for a complex, large-scale web crawling task. The target, `hepco-becker.de`, is a large e-commerce site with thousands of products across deeply nested categories.

A simple scraper would fail due to network interruptions, API failures, or sheer job length (potentially a multi-day crawl). This system is architected from the ground up for **resilience, network error handling, and stateful recovery**. It is designed to run as a standalone executable (`pyinstaller`) batch job, capable of being stopped and restarted without data loss.

## 2\. System Architecture & Core Components

The application operates as a stateful pipeline, where a central coordinator manages a series of specialized modules for network communication, data transformation, and storage.

### A. Coordinator (`main.py`)

  * **Job Orchestration:** The main entry point that initializes the `Logger` and `FileManager`.
  * **Task Selection:** Selects which specific crawl job to run (e.g., `start_luggage_systems_crawling`, `start_protection_comfort_crawling`).
  * **Environment Setup:** Creates the necessary output directories for the batch job, named with a timestamp (e.g., `./output/20251105_HB_PC/images`).

### B. Core Crawler Engine (`HB_crawler.py`)

  * **Stateful Logic:** This is the "brains" of the operation. It's not a stateless script; it reads a `_setting.csv` file to determine its **starting checkpoint** (`start_category`, `start_sub_category`). This allows the crawl to be resumed after a failure, saving hours or days of work.
  * **Crawl Strategy:** Implements two distinct, deep-crawl strategies:
    1.  By **Make/Model**: Iterates through every brand and model of vehicle.
    2.  By **Category/Sub-Category**: Iterates through product categories and handles pagination (`?p={page}`).
  * **Data Aggregation:** Holds the extracted data in a `pandas` DataFrame in memory, which is periodically flushed to disk.

### C. Advanced Network Manager (`web_driver_manager.py`)

This module is the core of the system's network-level capabilities and resilience.

  * **Dynamic Proxy Authentication:** The `create_driver` function **dynamically builds a `proxy_auth_plugin.zip` file on the fly**. It writes a custom `manifest.json` and `background.js` to handle complex proxy authentication (`username:password`) at the browser's `webRequest` level. This is a far more robust solution than standard proxy methods.
  * **Resilient Page Loader:** The `Driver.get_page` method wraps the Selenium `driver.get()` call in a **retry loop (10 attempts)** with a `try...except` block, ensuring temporary network failures do not kill the entire crawl.
  * **Resilient Image Downloader:** The `download_image` method (using `requests` for efficiency) also features a **5-attempt retry loop**. Crucially, it performs **data integrity validation** by checking the downloaded file size, automatically retrying if the file is empty or corrupted.

### D. External API Service (`translate_manager.py`)

  * **Data Transformation:** This module enriches the data by feeding the scraped English product descriptions (`item_description`) into the **Google Translate API** to produce a Korean translation (`trans_description`).
  * **Network Resilience:** This external HTTP API call has its *own* **5-attempt retry loop** with exponential backoff (`time.sleep(2)`). It's designed to handle API rate limiting or temporary service outages.

### E. Persistence & Logging (`file_manager.py`, `log_manager.py`)

  * **Safe Data Storage:** The crawler **periodically saves its complete DataFrame to an Excel file** (`save_database_to_excel`) *during* the crawl (e.g., after each model is finished). This minimizes data loss in the event of a critical failure.
  * **Advanced Logging:** The `log_manager` provides multi-level logging (`TRACE`, `DEBUG`, `INFO`) and separate build modes (`BUILD` vs. `DEBUG`) to control verbosity, saving all output to `log.txt` for troubleshooting.

## 3\. Highlights

This project was specifically designed to solve common networking and data integrity problems in large-scale scraping.

  * **Dynamic L7 Proxy Authentication:** Demonstrates a deep understanding of browser-level networking by programmatically generating a Chrome extension to handle `onAuthRequired` events for authenticated proxies.
  * **Multi-Layered Retry Logic:** The system does not assume a stable connection. Resilience is baked into three separate layers:
    1.  **Page Load:** Retries 10 times (`web_driver_manager`).
    2.  **Image Download:** Retries 5 times (`web_driver_manager`).
    3.  **API Translation:** Retries 5 times (`translate_manager`).
  * **Stateful Checkpointing:** The use of `_setting.csv` files to "bookmark" the crawler's progress is a key feature, turning a fragile script into a robust batch-processing job that can recover from failure.
  * **Data Integrity Validation:** By checking image file sizes post-download, the system ensures the data pipeline is not "garbage in, garbage out," preventing corrupted data from being saved.

## 4\. Tech Stack

  * **Core:** Python
  * **Web Automation:** Selenium
  * **Driver Management:** webdriver-manager
  * **Data Handling:** Pandas
  * **External API:** googletrans
  * **HTTP Requests:** requests
  * **System Utilities:** psutil (for `resource_monitor_manager`)
