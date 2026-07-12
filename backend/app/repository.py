from __future__ import annotations

import json
import sqlite3

from app.models import AiConfig, GeneratedContent, GenerationTask, PlatformAuthConfig


def save_ai_config(conn: sqlite3.Connection, config: AiConfig) -> None:
    conn.execute(
        """
        INSERT INTO ai_config (id, api_url, api_key, model, updated_at)
        VALUES (1, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(id) DO UPDATE SET
            api_url = excluded.api_url,
            api_key = excluded.api_key,
            model = excluded.model,
            updated_at = CURRENT_TIMESTAMP
        """,
        (config.api_url.strip(), config.api_key.strip(), config.model.strip()),
    )
    conn.commit()


def get_ai_config(conn: sqlite3.Connection) -> AiConfig | None:
    row = conn.execute(
        "SELECT api_url, api_key, model FROM ai_config WHERE id = 1",
    ).fetchone()
    if row is None:
        return None
    return AiConfig(api_url=row["api_url"], api_key=row["api_key"], model=row["model"])


def save_platform_auth_config(conn: sqlite3.Connection, config: PlatformAuthConfig) -> None:
    conn.execute(
        """
        INSERT INTO platform_auth_configs (
            platform, client_id, client_secret, redirect_uri, scopes, auth_url_template, updated_at
        ) VALUES (?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP)
        ON CONFLICT(platform) DO UPDATE SET
            client_id = excluded.client_id,
            client_secret = excluded.client_secret,
            redirect_uri = excluded.redirect_uri,
            scopes = excluded.scopes,
            auth_url_template = excluded.auth_url_template,
            updated_at = CURRENT_TIMESTAMP
        """,
        (
            config.platform.strip(),
            config.client_id.strip(),
            config.client_secret.strip(),
            config.redirect_uri.strip(),
            json.dumps(config.scopes, ensure_ascii=False),
            config.auth_url_template.strip(),
        ),
    )
    conn.commit()


def get_platform_auth_config(conn: sqlite3.Connection, platform: str) -> PlatformAuthConfig | None:
    row = conn.execute(
        """
        SELECT platform, client_id, client_secret, redirect_uri, scopes, auth_url_template
        FROM platform_auth_configs
        WHERE platform = ?
        """,
        (platform,),
    ).fetchone()
    if row is None:
        return None
    return PlatformAuthConfig(
        platform=row["platform"],
        client_id=row["client_id"],
        client_secret=row["client_secret"],
        redirect_uri=row["redirect_uri"],
        scopes=json.loads(row["scopes"]),
        auth_url_template=row["auth_url_template"],
    )


def list_platform_auth_configs(conn: sqlite3.Connection) -> list[PlatformAuthConfig]:
    rows = conn.execute(
        """
        SELECT platform, client_id, client_secret, redirect_uri, scopes, auth_url_template
        FROM platform_auth_configs
        ORDER BY platform
        """
    ).fetchall()
    return [
        PlatformAuthConfig(
            platform=row["platform"],
            client_id=row["client_id"],
            client_secret=row["client_secret"],
            redirect_uri=row["redirect_uri"],
            scopes=json.loads(row["scopes"]),
            auth_url_template=row["auth_url_template"],
        )
        for row in rows
    ]


def save_generated_contents(
    conn: sqlite3.Connection,
    task: GenerationTask,
    contents: list[GeneratedContent],
) -> None:
    conn.executemany(
        """
        INSERT INTO generated_history (
            product_name, content_type, platform, title, body, tags, keywords,
            image_suggestions, publish_tip, optional_script, image_assets
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        [
            (
                task.product_name,
                task.content_type,
                item.platform,
                item.title,
                item.body,
                json.dumps(item.tags, ensure_ascii=False),
                json.dumps(item.keywords, ensure_ascii=False),
                json.dumps(item.image_suggestions, ensure_ascii=False),
                item.publish_tip,
                item.optional_script,
                json.dumps([asset.__dict__ for asset in item.image_assets], ensure_ascii=False),
            )
            for item in contents
        ],
    )
    conn.commit()


def list_history(conn: sqlite3.Connection) -> list[dict]:
    rows = conn.execute(
        """
        SELECT id, product_name, content_type, platform, title, body, tags, keywords,
               image_suggestions, publish_tip, optional_script, image_assets, created_at
        FROM generated_history
        ORDER BY id DESC
        LIMIT 50
        """
    ).fetchall()
    return [
        {
            **dict(row),
            "tags": json.loads(row["tags"]),
            "keywords": json.loads(row["keywords"]),
            "image_suggestions": json.loads(row["image_suggestions"]),
            "image_assets": json.loads(row["image_assets"]),
        }
        for row in rows
    ]
