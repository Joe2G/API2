const express = require('express');
const cors = require('cors');
const ytdl = require('ytdl-core');
const { sanitizeFilename } = require('sanitize-filename');
const app = express();
const port = process.env.PORT || 8000;

app.use(express.json());
app.use(cors());

const origins = [
    "https://joe2g.github.io",
];

app.use(cors({
    origin: origins,
    credentials: true,
}));

app.post('/download', async (req, res) => {
    const { url, type } = req.body;

    if (!url || !type || !['video', 'audio'].includes(type)) {
        return res.status(400).json({ error: "Invalid 'url' or 'type' provided. Use 'video' or 'audio'." });
    }

    try {
        const info = await ytdl.getInfo(url);
        let stream;
        if (type === 'video') {
            stream = ytdl(url, { quality: 'highestvideo' });
        } else {
            stream = ytdl(url, { quality: 'highestaudio' });
        }

        const title = info.videoDetails.title;
        const filename = `${sanitizeFilename(title)}.${type === 'video' ? 'mp4' : 'mp3'}`;

        res.set({
            'Content-Disposition': `attachment; filename="${filename}"`,
            'Content-Type': type === 'video' ? 'video/mp4' : 'audio/mpeg',
        });

        stream.pipe(res);

    } catch (error) {
        console.error("Error occurred during download:", error);
        res.status(500).json({ error: "An error occurred during the download process." });
    }
});

app.listen(port, () => {
    console.log(`Server is running on port ${port}`);
});
