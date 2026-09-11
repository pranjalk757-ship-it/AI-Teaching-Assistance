import subprocess

playlist_url = "https://youtube.com/playlist?list=PLBlnK6fEyqRgMCUAG0XRw78UA8qnv6jEx&si=yev3vxaqX6h5pdAD"

results = subprocess.run(["yt-dlp","--flat-playlist","--print","%(webpage_url)s",playlist_url],
               capture_output=True,
               text=True)

urls = results.stdout.split()

with open("video_urls.txt",'w') as file:
    for url in urls[:10]:
        file.write(url+"\n")