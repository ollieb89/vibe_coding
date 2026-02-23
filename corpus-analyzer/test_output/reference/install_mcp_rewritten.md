---
title: MCP Server Installation for SuperClaude
description: A module to install and manage MCP servers using the latest Claude Code API.
tags: [cli, superclaude, mcp, installation]
source: src/superclaude/cli/install_mcp.py
---

# MCP Server Installation for SuperClaude

This module allows you to install and manage MCP servers using the latest Claude Code API. It is based on the installer logic from commit `d4e871a` but has been updated for improved functionality.

## Prerequisites

Before you begin, ensure that your environment meets the following prerequisites:

- Python 3.x
- Claude Code CLI installed and configured

## Available MCP Servers

The following MCP servers are available for installation:

1. [Algolia Search](#algolia-search)
2. [AWS Amplify](#aws-amplify)
3. [Firebase](#firebase)
4. [Google Cloud Functions](#google-cloud-functions)
5. [Microsoft Azure Functions](#microsoft-azure-functions)
6. [SendGrid Email API](#sendgrid-email-api)
7. [Twilio API](#twilio-api)

### Algolia Search

Algolia is a powerful search engine that can be integrated into your application to provide fast and relevant search results.

#### Installation

To install the Algolia MCP server, use the following command:

```bash
claude mcp add --transport local algolia
```

### AWS Amplify

AWS Amplify is a set of tools and services that enable mobile and front-end web development.

#### Installation

To install the AWS Amplify MCP server, use the following command:

```bash
claude mcp add --transport local aws-amplify
```

### Firebase

Firebase is a mobile and web application development platform that provides real-time database, authentication, cloud storage, and more.

#### Installation

To install the Firebase MCP server, use the following command:

```bash
claude mcp add --transport local firebase
```

### Google Cloud Functions

Google Cloud Functions is a serverless execution environment for building and connecting cloud services.

#### Installation

To install the Google Cloud Functions MCP server, use the following command:

```bash
claude mcp add --transport local google-cloud-functions
```

### Microsoft Azure Functions

Microsoft Azure Functions is a serverless compute service that lets you run code on-demand without having to explicitly provision or manage infrastructure.

#### Installation

To install the Microsoft Azure Functions MCP server, use the following command:

```bash
claude mcp add --transport local microsoft-azure-functions
```

### SendGrid Email API

SendGrid is a cloud-based email delivery platform that enables developers to send emails with ease.

#### Installation

To install the SendGrid Email API MCP server, use the following command:

```bash
claude mcp add --transport local sendgrid
```

### Twilio API

Twilio is a cloud communications platform that enables developers to build communication applications using APIs.

#### Installation

To install the Twilio API MCP server, use the following command:

```bash
claude mcp add --transport local twilio
```

## Installing Multiple Servers

You can also install multiple servers at once by providing a list of server names as arguments to the `claude mcp add` command. For example, to install both Algolia Search and Firebase:

```bash
claude mcp add --transport local algolia firebase
```

## Interactive Selection

If you do not provide a list of servers to install, the module will prompt you to select the servers you wish to install interactively.

## Dry Run

To perform a dry run (i.e., simulate the installation process without actually installing anything), use the `--dry-run` flag:

```bash
claude mcp add --transport local algolia --dry-run
```

[source: src/superclaude/cli/install_mcp.py]