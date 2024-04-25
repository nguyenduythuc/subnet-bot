1. Clone the project
2. Install requirements dependencies:
    ```bash
    pip install -r requirements.txt
3. Update keys/envs in bots
4. Running the bots:
   ```bash
   pm2 start python3 -n noti -- ./noti.py
   pm2 start python3 -n checkServerOnline -- ./checkServerOnline.py
