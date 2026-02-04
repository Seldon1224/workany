#!/usr/bin/env python3
"""Simple test script to verify API functionality."""
import asyncio
import httpx


async def test_health():
    """Test health endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:2026/health")
        print(f"Health check: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_root():
    """Test root endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:2026/")
        print(f"\nRoot endpoint: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def test_files_skills_dir():
    """Test files skills directory endpoint."""
    async with httpx.AsyncClient() as client:
        response = await client.get("http://localhost:2026/files/skills-dir")
        print(f"\nSkills dir: {response.status_code}")
        print(f"Response: {response.json()}")
        return response.status_code == 200


async def main():
    """Run all tests."""
    print("🧪 Testing WorkAny API (Python)\n")
    print("=" * 50)
    
    try:
        results = []
        results.append(await test_health())
        results.append(await test_root())
        results.append(await test_files_skills_dir())
        
        print("\n" + "=" * 50)
        if all(results):
            print("✅ All tests passed!")
        else:
            print("❌ Some tests failed")
            return 1
        
        return 0
    except Exception as e:
        print(f"\n❌ Error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)
