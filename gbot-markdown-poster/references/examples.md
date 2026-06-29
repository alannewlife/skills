# MarkdownPoster Integration Examples

## Basic Usage

### Open a single file
```bash
python3 scripts/mdp.py open README.md
```

### Generate URL for sharing
```bash
python3 scripts/mdp.py open document.md --channel hash --no-open
```

### Test the bundled sample with a local image
```bash
python3 scripts/mdp.py open references/sample-with-image
```

The sample directory contains `index.md` and `assets/sample.svg`, so it is a
quick smoke test for the default bridge import and local image handling.

## Integration with Other Skills

### With markdown-to-html
```bash
# Convert markdown to HTML, then view in MarkdownPoster
python3 scripts/mdp.py open converted.md
```

### With doc-coauthoring
```bash
# After drafting documentation, preview in MarkdownPoster
python3 scripts/mdp.py open draft.md
```

## Workflow Examples

### 1. Documentation Preview
```bash
# Write documentation
cat > docs/api.md << 'EOF'
# API Documentation

## Endpoints

### GET /users
Returns list of users.

### POST /users
Creates a new user.
EOF

# Preview in MarkdownPoster
python3 scripts/mdp.py open docs/api.md
```

### 2. Share Markdown Content
```bash
# Generate shareable URL
URL=$(python3 scripts/mdp.py open content.md --channel hash --no-open | sed -n 's/^MarkdownPoster hash URL: //p')
echo "Share this URL: $URL"
```

### 3. Batch Processing
```bash
# Open multiple files
for file in docs/*.md; do
    python3 scripts/mdp.py open "$file" --channel hash --no-open
done
```

## Custom Instances

### Self-hosted MarkdownPoster
```bash
python3 scripts/mdp.py open content.md \
    --base-url https://your-instance.com/mdp/import
```

### Local development server
```bash
python3 scripts/mdp.py open content.md \
    --base-url http://localhost:3000/import
```

## Tips

1. **Large files**: For very large Markdown files (>1MB), consider splitting them
2. **Images**: MarkdownPoster supports images via URLs or base64 encoding
3. **Themes**: MarkdownPoster provides multiple themes for different viewing styles
4. **Export**: Use MarkdownPoster's built-in export to save as image or PDF
