
![Python](https://img.shields.io/badge/Python-3.8%2B-3776AB?logo=python&logoColor=white)
![License](https://img.shields.io/badge/License-MIT-4DC71F?logo=open-source-initiative&logoColor=white)
![Status](https://img.shields.io/badge/Status-Active%20Development-FF6B35?logo=git&logoColor=white)
![Contributions](https://img.shields.io/badge/Contributions-Welcome-8B5DFF?logo=github&logoColor=white)

# BrokenRx

**BrokenRx** is an advanced cybersecurity challenge designed with the target of displaying advanced vulnerability discovery, secure coding practice, insecure
coding knowledge, exploitatino accuracy, creativity and realworld attack simulation.

**BrokenRx** is designed to display the chain of OAuth PKCE misuse leading to code interception and session fixation. It is based on a pharmacy medication delivery portal designed for this specific project. This pharmacy medication delivery portal has the capability to register clients / users who will upload their prescriptions which will be evaluated by an admin an approved for delivery. The authentication and authorization of the users is handled by an oauth system which is designed to include the vulnerability.



## Table of Contents

- [Project Mirage](#project-mirage)
  - [Table of Contents](#table-of-contents)
  - [Key Features](#key-features)
  - [Environment](#environment)
  - [Installation](#installation)
    - [1. Repository](#1-repository)
    - [2. Running App](#2-running-app)
      - [Using Script](#using-script)
      - [Manually Starting Each Server](#manual-server)
            - [Run Main App](#main-app)
            - [Run API Server](#api-server)
            - [Run Auth Server](#auth-server)
  - [Usage](#usage)
  - [Project Structure](#project-structure)
  - [Mitigation](#mitigation)
  - [Warning](#warning)

## Key Features

- **Interntionally Vulernable web app**
- **OAuth Implementation**: Intentionally vulnerable OAuth Implementaion
- **Manual and Automated Exploits**: Proof of Concept Scripts which allow atomated and manual exploitation of the vulnerability
- **Mitigation**: Code Integration to mitigate the vulnerabilities

## Environment

- **OS:** Kali Linux 2025.3 (tested)  
- **Python:** 3.13.9 

## Installation and Usage

### 1. Repository
- Clone the repository
```bash
git clone https://github.com/bek2518/BrokenRx; cd BrokenRx
```
- Make sure all requirements are fulfilled
```bash
pip install -r requirements.txt
```
### 2. Running App
#### Using Script
- On the project root or BrokenRx run the script BrokenRx.sh
```bash
chmod u+x BrokenRx.sh
./BrokenRx.sh
```
- When running the script it will ask for an admin username, password and email which will assign an admin level access in the app


#### Manually Starting Each Server
##### Run Main App
```bash
python3 app.y
```
##### Run API Server
```bash
uvicorn api:app --reload --port 9000
```

##### Run Auth Server
```bash
cd AuthServer
uvicorn auth_app:app --relaod --port 8000
```

## Usage
- After all servers are running navigate to the endpoint http://localhost:5000 to access the web app

## Exploiting Vulnerability
- While a victim session is open in a browser run the exploit in console to receive the malicious link to deliver to the victim
```bash
cd Exploit
python3 poc.py
```
- Running the poc will provide with the malicious link and starts a server awaiting callback
- Open the malicious link provided in the browser of the victim
- Back on the termianal, acess token will be delivered with successful exploitation.
- To confirm the authorization code works, open a separate web browser and navigate to http://localhost:5000 and open dev tools and add the access token received as cookie and reload and navigate to dashboard which will effectively login attacker as victim.
- The callback code is not revoked so it can be reused again to demonstrate that, after going thorugh the process above make note of the pkce_verifier provided
- On terminal run the manual.py which requests code which is the callback code received and the pkce_verifier which we have noted
```bash
python3 manual.py
```
- Provide both codes and receive authorization tokens unlimited times


## Project Structure

```
Project_Mirage/
├── .pids/ 
├── AuthServer/       
    ├── app/ 
        ├── templates/
            ├── login.html
            ├── register.html
        ├── auth.py
    ├── models/
        ├── storage/ 
            ├── oauthdb.db
        ├── auth_database.py
        ├── auth_db_handler.py  
    ├── .env.auth
    ├── auth_app.py
    ├── create_admin.py   
    ├── private.pem
├── Exploit/
    ├── .env.exploit
    ├── manual.py
    ├── poc.py
├── models/
    ├── storage/
        ├── prescriptions/
        ├── BrokenRx.db
    ├── database.py
    ├── db_handler.py
├── templates/
    ├── resources/
    ├── admin.html
    ├── base.html
    ├── dashboard.html
    ├── landing_page.html
    ├── upload.html
├── .env
├── .gitignore
├── api.py
├── app.py
├── auth.py
├── BrokenRx.sh
├── public.pem
├── README.md
├── requirements.txt
└── terminate.sh
```

## Mitigation
- The first main problem is the lack of redirect_uri confirmation which the app should have validation of the the redirect_uri from a database of allowed callback address
- If the redirect_uri is not in the list the request should be either completely rejected or based on the client_id the redirect_uri should be rewritten to the correct it
- To fix the code reuse, making the code single use only with the code being effectively distroyed when the request to the callback endpoint is made with the code
- Both fixes should be implemented to effectively remove this vulnerability
- To see the implementation of these mitigations:
    - Open the AuthServer/auth_app.py
    - Navigate to the /authorize (starting from line 133) endpoint and uncomment Fix No 1 and try the exploit, then try Fix 2
    - On the same script navigate to /token (starting from line 184) and uncomment the Fix lines for removal of authorization code and try the code reuse

## Warning

> ⚠️ **This project is designed for educational and research purposes. The web app, oauth server and exploit scripts are specifically designed for this vulnerable application and not real-world application.**

