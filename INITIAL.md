## FEATURE:

- "Open Eats" a recipies PWA / website where you can save your recipies to a personal cookbook; with the option to include your recipe for other people to use in the "Open Eats" cookbook.
- Each recipe should show how long it takes to make, and how many people it feeds.
- An upvote/downvote ranking system for people that have made the recipe so people can find new enjoyable recipies.
- Tags to filter recipies by high protein, gluten-free, lunch, dinner, breakfast, mealprep, "crunchy mom friendly", ect.
- Ability to group recipies with similar ingredients to make a shopping list.

## TECH STACK:
- Backend
  - Python, PostgreSQL and RESTFUL `FastAPI`, using `pydantic` for data validation. 
- Frontend
    - React, Tailwind, Vite
    - Flowbite for frontend components.
- Deployment
  - Docker

## EXAMPLES:

[Provide and explain examples that you have in the `examples/` folder]

## DOCUMENTATION:

[List out any documentation (web pages, sources for an MCP server like Crawl4AI RAG, etc.) that will need to be referenced during development]

## OTHER CONSIDERATIONS:

- Eventually, there will be a Chrome extension that will scan a webpage for recipies and add it to your recipe book, so keep that in mind.
- I may eventually decide to make an android/Iphone app to go along with this, so ensure the structure is able to handle an app in the future.
- Include a .env.example, README with instructions for setup including how to configure Gmail and Brave.
- Include the project structure in the README.
- Eventually, I would like some way of automating what meals are tagged as, so be sure to keep that in mind for the app structure.
