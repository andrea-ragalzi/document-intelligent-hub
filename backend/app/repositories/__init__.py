"""
Repository Layer - Data Access Abstraction

This package contains repository classes that encapsulate all data access logic.
Repositories provide a clean interface for CRUD operations on data stores.

Architecture Benefits:
- Single Responsibility: All database operations in one place
- Testability: Easy to mock for unit tests
- Maintainability: Changes to data layer don't affect services
- Microservices-Ready: Can be replaced with remote data access
"""
