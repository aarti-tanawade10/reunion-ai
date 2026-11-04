### ReunionAI: Project Documentation

# Overview

ReunionAI is a web application that helps a geographically scattered group of friends choose a fair meeting location for a reunion. The organizer enters each friend’s name and home city, along with the preferred dates, the desired atmosphere and a budget. The application calculates the travel distance from every friend’s city to a set of candidate cities and ranks the three most suitable options. It then uses the Claude API to write a short invitation message and a day-by-day itinerary for the best-ranked city.

#How the Ranking Works

For each candidate city, the application adds up the distance every friend would travel and adds half of the longest single trip. This keeps the total travel low while preventing one person from having to cross the country. The city with the lowest score is recommended.
