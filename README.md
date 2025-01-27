# RaGPT: AI Assistant for Production Analytics

## Installation
In order to run the notebook, it is required to have the proprietary API running. To run it locally we refer the user [here](https://github.com/sa-team-d/api), as he can find all the documentation needed. Make sure to follow the instructions correctly and to have the API running locally, as this is a strict requirement for the notebook to be running.

## Overview
This project comes from the idea of improving the already existing AI assistant built by a group of students of the University of Pisa, for a management system of a production site. Their work can be found [here](https://github.com/sa-team-d/rag).

RaGPT is a refined AI assistant designed to enhance production site analytics by providing a streamlined and practical workflow. It builds upon the initial RAG (Retrieval-Augmented Generation) architecture to deliver a more versatile system capable of general-purpose queries, KPI computation, insights, and actionable suggestions for improving production efficiency.

## Features
- **General Queries**: Provides basic information about the production site, such as machine counts and categories.
- **KPI Computation and Comparison**: Computes specific KPIs for machines over custom time periods and compares performance.
- **Insight Generation**: Offers actionable insights and suggestions based on production data.
- **Integration with Real-Time Data**: Links with other group implementations to retrieve and analyze live production data.

## Implementation
- **OpenAI API**: Utilizes the `gpt-4o-mini` model with file search and function-calling capabilities for enhanced performance.
- **Knowledge Base**: Data from the original MongoDB database has been structured into a JSON file for fast retrieval.
- **Tools**:
  - `file_search`: Implements a retrieval-based approach for document queries.
  - `function_calling`: Executes user-defined functions to compute KPIs and process queries.

### Workflow
1. Parse user query and determine required actions.
2. Retrieve relevant data using the `file_search` tool.
3. Call necessary functions for computations or insights.
4. Return responses seamlessly combining retrieval and generative AI.

## Example Queries
- "How many machines are there?"
- "What is the cost of all machines in September 2024?"
- "Which machine has been the least efficient last month?"
- "What can be done to improve overall production efficiency?"

## Advantages
1. **Slimmer Design**: Eliminates the need for a local vector store.
2. **Flexible Workflow**: Adapts to a wide range of queries without structural changes.
3. **State-of-the-Art Performance**: Leverages advanced language model capabilities.
4. **Future-Proof**: Benefits from continuous improvements in OpenAI's API features.

## Limitations
- **External Dependency**: Relies on OpenAI's API, introducing potential service dependencies.
- **Beta Features**: Some instability due to the experimental nature of certain API capabilities.
- **Cost**: Minimal costs for token usage in API requests.

## Insights and Suggestions
The assistant effectively combines retrieval-based and generative capabilities to answer both simple and complex questions, making it a versatile tool for production analytics.

## Future Enhancements
- Automating knowledge base updates.
- Integrating additional KPI generation tools for comprehensive reporting.
- Extending support for advanced queries and insights.

## Conclusion
RaGPT represents a significant improvement over the original RAG-based implementation, offering a flexible and efficient solution tailored to the needs of modern production environments.
