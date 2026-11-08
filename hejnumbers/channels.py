"""Zeigt deine Buffer-Kanäle mit ID an. Die IDs trägst du in config.json ein."""
from .buffer_api import list_channels

if __name__ == "__main__":
    for org, chans in list_channels():
        print(f"\nOrganisation: {org['name']}")
        for c in chans:
            print(f"  {c['service']:<12} {c.get('displayName') or c['name']:<30} ID: {c['id']}")
