"""initialize_application_architecture

Revision ID: fc6f9fa4a664
Revises: 
Create Date: 2025-08-09 16:58:36.142720

"""
import sqlalchemy as sa

from alembic import op

# revision identifiers, used by Alembic.
revision = 'fc6f9fa4a664'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Check if we're using SQLite
    is_sqlite = False
    if op.get_context().dialect.name == 'sqlite':
        is_sqlite = True
    
    # Create users table
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("email", sa.String(), nullable=False),
        sa.Column("hashed_password", sa.String(), nullable=False),
        sa.Column("is_active", sa.Boolean(), default=True, nullable=True),
        sa.Column("is_superuser", sa.Boolean(), default=False, nullable=True),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_users_email"), "users", ["email"], unique=True)
    op.create_index(op.f("ix_users_id"), "users", ["id"], unique=False)

    # Create trigger function for updating updated_at field - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE OR REPLACE FUNCTION update_updated_at_column()
            RETURNS TRIGGER AS $$
            BEGIN
                NEW.updated_at = NOW();
                RETURN NEW;
            END;
            $$ language 'plpgsql';
        """)

        # Create trigger on users table - PostgreSQL only
        op.execute("""
            CREATE TRIGGER update_users_updated_at
            BEFORE UPDATE ON users
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create projects table
    op.create_table(
        "projects",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column(
            "project_type",
            sa.Enum(
                "DYNAMIC",
                "CINEMATIC",
                "DOCUMENTARY",
                "SOCIAL",
                "CUSTOM",
                name="projecttype",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "EXPORTED",
                name="projectstatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("timeline_data", sa.JSON(), nullable=True),
        sa.Column("total_duration", sa.Float(), nullable=True),
        sa.Column("processing_progress", sa.Float(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_projects_id"), "projects", ["id"], unique=False)

    # Create trigger on projects table - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE TRIGGER update_projects_updated_at
            BEFORE UPDATE ON projects
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create videos table
    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False),
        sa.Column("height", sa.Integer(), nullable=False),
        sa.Column("fps", sa.Float(), nullable=False),
        sa.Column(
            "codec",
            sa.Enum("H264", "H265", "VP9", "AV1", name="videocodec", native_enum=False),
            nullable=False,
        ),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column(
            "status",
            sa.Enum(
                "UPLOADING",
                "UPLOADED",
                "PROCESSING",
                "ANALYZED",
                "FAILED",
                name="videostatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("analysis_data", sa.JSON(), nullable=True),
        sa.Column("scene_cuts", sa.JSON(), nullable=True),
        sa.Column("audio_analysis", sa.JSON(), nullable=True),
        sa.Column("face_detections", sa.JSON(), nullable=True),
        sa.Column("emotion_analysis", sa.JSON(), nullable=True),
        sa.Column("text_detections", sa.JSON(), nullable=True),
        sa.Column("object_detections", sa.JSON(), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_videos_id"), "videos", ["id"], unique=False)

    # Create trigger on videos table - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE TRIGGER update_videos_updated_at
            BEFORE UPDATE ON videos
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create audios table
    op.create_table(
        "audios",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("filename", sa.String(), nullable=False),
        sa.Column("original_filename", sa.String(), nullable=False),
        sa.Column("title", sa.String(), nullable=True),
        sa.Column("description", sa.String(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=True),
        sa.Column("user_id", sa.Integer(), nullable=False),
        sa.Column("file_path", sa.String(length=500), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("mime_type", sa.String(length=100), nullable=False),
        sa.Column("duration", sa.Float(), nullable=False),
        sa.Column(
            "codec",
            sa.Enum("MP3", "AAC", "FLAC", "WAV", "OGG", name="audiocodec", native_enum=False),
            nullable=False,
        ),
        sa.Column("bitrate", sa.Integer(), nullable=True),
        sa.Column("sample_rate", sa.Integer(), nullable=False),
        sa.Column("channels", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "UPLOADING",
                "UPLOADED",
                "PROCESSING",
                "ANALYZED",
                "FAILED",
                name="audiostatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("analysis_data", sa.JSON(), nullable=True),
        sa.Column("transcription", sa.Text(), nullable=True),
        sa.Column("silence_detection", sa.JSON(), nullable=True),
        sa.Column("volume_analysis", sa.JSON(), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("analyzed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.ForeignKeyConstraint(
            ["user_id"],
            ["users.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_audios_id"), "audios", ["id"], unique=False)

    # Create trigger on audios table - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE TRIGGER update_audios_updated_at
            BEFORE UPDATE ON audios
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create cutting_plans table
    op.create_table(
        "cutting_plans",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "DRAFT",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                name="cuttingplanstatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column("plan_data", sa.JSON(), nullable=True),
        sa.Column("total_duration", sa.Float(), nullable=True),
        sa.Column("estimated_output_duration", sa.Float(), nullable=True),
        sa.Column("cutting_strategy", sa.String(), nullable=True),
        sa.Column("ai_parameters", sa.JSON(), nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_cutting_plans_id"), "cutting_plans", ["id"], unique=False)

    # Create trigger on cutting_plans table - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE TRIGGER update_cutting_plans_updated_at
            BEFORE UPDATE ON cutting_plans
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)

    # Create export_jobs table
    op.create_table(
        "export_jobs",
        sa.Column("id", sa.Integer(), nullable=False),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("project_id", sa.Integer(), nullable=False),
        sa.Column(
            "status",
            sa.Enum(
                "PENDING",
                "PROCESSING",
                "COMPLETED",
                "FAILED",
                "CANCELLED",
                name="exportstatus",
                native_enum=False,
            ),
            nullable=True,
        ),
        sa.Column(
            "format",
            sa.Enum("MP4", "MOV", "AVI", "WEBM", "MKV", name="exportformat", native_enum=False),
            nullable=False,
        ),
        sa.Column(
            "quality",
            sa.Enum("LOW", "MEDIUM", "HIGH", "ULTRA", name="exportquality", native_enum=False),
            nullable=False,
        ),
        sa.Column("output_width", sa.Integer(), nullable=True),
        sa.Column("output_height", sa.Integer(), nullable=True),
        sa.Column("output_fps", sa.Float(), nullable=True),
        sa.Column("output_bitrate", sa.Integer(), nullable=True),
        sa.Column("output_filename", sa.String(), nullable=True),
        sa.Column("output_file_path", sa.String(length=500), nullable=True),
        sa.Column("output_file_size", sa.BigInteger(), nullable=True),
        sa.Column("export_settings", sa.JSON(), nullable=True),
        sa.Column("progress_percentage", sa.Float(), default=0.0, nullable=True),
        sa.Column("processing_time", sa.Float(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("CURRENT_TIMESTAMP"),
            nullable=True,
        ),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(
            ["project_id"],
            ["projects.id"],
        ),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_export_jobs_id"), "export_jobs", ["id"], unique=False)

    # Create trigger on export_jobs table - PostgreSQL only
    if not is_sqlite:
        op.execute("""
            CREATE TRIGGER update_export_jobs_updated_at
            BEFORE UPDATE ON export_jobs
            FOR EACH ROW
            EXECUTE FUNCTION update_updated_at_column();
        """)


def downgrade() -> None:
    # Drop tables in reverse order to avoid foreign key constraint issues
    op.drop_table("export_jobs")
    op.drop_table("cutting_plans")
    op.drop_table("audios")
    op.drop_table("videos")
    op.drop_table("projects")
    op.drop_table("users")
    
    # Drop trigger function if it exists - PostgreSQL only
    if op.get_context().dialect.name != 'sqlite':
        op.execute("DROP FUNCTION IF EXISTS update_updated_at_column() CASCADE;")