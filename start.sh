while ! (ping -c 1 -W 1 1.2.3.4 | grep -q 'statistics'); do
    echo "Waiting for 1.2.3.4 - network interface might be down..."
    sleep 1
done

cd /home/pi/ws/invabot
python bot.py
