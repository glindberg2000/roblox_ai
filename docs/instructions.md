

Product Specification

Project Overview

This Roblox project is designed with:

	1.	AI-Driven NPC Interactions: Utilizes an API to handle AI-generated responses for NPCs in the game.
	2.	Dashboard for Asset and NPC Management: The dashboard enables the management of assets and NPCs, including asset uploads and editing.

Primary Objectives

	1.	Fix Dashboard Asset Editing: Ensure asset edit functionality works correctly.
	2.	Database Streamlining:
	•	Update File Naming: Use lowercase original filenames for assets instead of the assetID.
	•	Asset Storage Path: Relocate asset storage to the src/assets directory structure.
	•	Remove Unnecessary Fields: Remove unused or confusing database fields for clarity.
	3.	File Accessibility for Lua Code: Ensure assets are accessible from src/assets, not api/, to allow Lua access.

Development Plan & Next Steps

1. Dashboard Improvements

	•	Goal: Make the asset edit functionality work and improve the file upload flow.
	•	Steps:
	1.	Inspect Current Asset Edit Code: Identify why the edit function is not executing and fix issues.
	2.	Modify Edit Button: Ensure it links correctly to the database entries in src/assets.
	3.	Refactor Upload Process: Streamline the file upload to use lowercase filenames by default.
	4.	Testing Checkpoint 1: Verify that asset edit and upload functions are working, with correct filenames and storage paths.

2. Database Optimization

	•	Goal: Adjust the database structure to enhance file accessibility, reduce confusion, and streamline usage.
	•	Steps:
	1.	Rename Files: Set uploaded assets to use lowercase original filenames rather than assetID.
	2.	Update Paths: Move stored assets to src/assets, ensuring Lua scripts can access them.
	3.	Remove Unused Fields: Identify and remove non-essential fields, clarifying database purpose.
	4.	Testing Checkpoint 2: Test for seamless data retrieval and edit capabilities from the dashboard, checking path alignment and proper asset name formats.

3. Testing & WIP Checkpoints

	•	Goal: Set incremental checkpoints for thorough testing, allowing early detection of issues.
	•	Checkpoints:
	•	Checkpoint 1: Asset editing and upload with lowercase filenames.
	•	Checkpoint 2: Database optimizations verified, ensuring only essential fields remain.
	•	Checkpoint 3: File accessibility verified for Lua code, ensuring assets load correctly.
