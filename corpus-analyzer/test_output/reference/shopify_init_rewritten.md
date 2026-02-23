---
title: Shopify Project Initialization Script
description: Interactive script to scaffold Shopify apps, extensions, or themes. Supports environment variable loading from multiple locations.
tags: shopify, development, python, scripts
source: skills/shopify-development/scripts/shopify_init.py
---

# Shopify Project Initialization Script

This script provides an interactive interface to scaffold Shopify apps, extensions, or themes. It supports environment variable loading from multiple sources in priority order.

## Configuration Options
- `SHOPIFY_API_KEY`: Your Shopify API key (required)
- `SHOPIFY_API_SECRET`: Your Shopify API secret (required)
- `SHOP_DOMAIN`: The domain of your Shopify store (optional, defaults to "your-store.myshopify.com")
- `ACCESS_SCOPES`: Comma-separated list of access scopes for the app (optional, defaults to "read_products,write_products")

## Project Types

The script can initialize three types of projects:

1. **App**: A custom Shopify app that extends store functionality.
2. **Extension**: A UI extension that adds new features or modifies existing ones in the Shopify admin or checkout.
3. **Theme**: A custom Shopify theme to change the look and feel of your store.

## Instructions

1. Run the script from the command line: `python shopify_init.py`
2. Follow the prompts to select a project type, provide necessary details, and choose access scopes for an app (if applicable).
3. The script will create the required files and directories, and print instructions on how to proceed with setting up your new project.

## Usage Example

```bash
$ python shopify_init.py
Shopify Project Initializer
===========================

... (interactive prompts for project type, name, scopes, etc.)

Next steps:
  cd my-shopify-app
  npm install
  shopify app dev
```

[source: skills/shopify-development/scripts/shopify_init.py]