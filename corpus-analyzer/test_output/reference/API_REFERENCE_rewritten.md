---
title: Playwright Skill - Complete API Reference
source: skills/playwright-skill/API_REFERENCE.md
---

# Playwright Testing Framework API Reference

This is an extensive guide to using the Playwright Testing Framework for web automation and testing. It covers various aspects such as navigation, interaction, assertions, network requests, visual testing, and mobile testing.

## Table of Contents
1. [Introduction](#introduction)
2. [Setup](#setup)
3. [Navigation](#navigation)
   - [Go to a URL](#goto-a-url)
   - [Reload the page](#reload-the-page)
4. [Interaction](#interaction)
   - [Click an element](#click-an-element)
   - [Type text into an input field](#type-text-into-an-input-field)
   - [Fill a form](#fill-a-form)
   - [Submit a form](#submit-a-form)
   - [Hover over an element](#hover-over-an-element)
   - [Scroll to an element](#scroll-to-an-element)
5. [Assertions](#assertions)
   - [Check the page title](#check-the-page-title)
   - [Check the current URL](#check-the-current-url)
   - [Check if an element is visible](#check-if-an-element-is-visible)
   - [Check if an element contains text](#check-if-an-element-contains-text)
   - [Check the value of an input field](#check-the-value-of-an-input-field)
   - [Check the attribute of an element](#check-the-attribute-of-an-element)
   - [Check CSS properties of an element](#check-css-properties-of-an-element)
   - [Check the count of elements](#check-the-count-of-elements)
   - [Check if a checkbox or radio button is checked](#check-if-a-checkbox-or-radio-button-is-checked)
6. [Waiting Strategies](#waiting-strategies)
   - [Wait for an element to be visible](#wait-for-an-element-to-be-visible)
   - [Wait for a specific condition](#wait-for-a-specific-condition)
   - [Wait for network activity](#wait-for-network-activity)
   - [Wait for a JavaScript function to complete](#wait-for-a-javascript-function-to-complete)
7. [Page Object Model (POM)](#page-object-model-pom)
8. [Network & API Testing](#network--api-testing)
   - [Intercept requests](#intercept-requests)
   - [Modify requests](#modify-requests)
   - [Block resources](#block-resources)
9. [Visual Testing](#visual-testing)
   - [Take a screenshot of the page](#take-a-screenshot-of-the-page)
   - [Compare an image to a baseline for visual regression testing](#compare-an-image-to-a-baseline-for-visual-regression-testing)
10. [Mobile Testing](#mobile-testing)
    - [Emulate mobile devices](#emulate-mobile-devices)

## Introduction
This guide provides an overview of the Playwright Testing Framework, a powerful tool for automating web browsers and testing web applications. It supports Chromium, Firefox, and WebKit browsers across various platforms and devices.

[source: skills/playwright-skill/API_REFERENCE.md]