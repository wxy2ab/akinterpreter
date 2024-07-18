from typing import List
import duckdb
from ..model.project_model import Project, Chat

class ProjectDB:
    def __init__(self, db_file='./databse/projects.db'):
        self.conn = duckdb.connect(db_file)
        self._create_tables()

    def _create_tables(self):
        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS projects (
            id INTEGER PRIMARY KEY,
            session_id VARCHAR UNIQUE NOT NULL,
            create_date TIMESTAMP NOT NULL,
            project_id VARCHAR UNIQUE NOT NULL,
            owner VARCHAR NOT NULL
        )
        """)

        self.conn.execute("""
        CREATE TABLE IF NOT EXISTS chats (
            id INTEGER PRIMARY KEY,
            project_id INTEGER NOT NULL,
            message TEXT,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (project_id) REFERENCES projects(id)
        )
        """)

    def insert_project(self, project: Project):
        self.conn.execute("""
        INSERT INTO projects (session_id, create_date, project_id, owner)
        VALUES (?, ?, ?, ?)
        """, (project.session_id, project.create_date, project.project_id, project.owner))
        
        # Get the last inserted id
        project.id = self.conn.execute("SELECT last_insert_rowid()").fetchone()[0]

    def insert_chat(self, chat: Chat):
        self.conn.execute("""
        INSERT INTO chats (project_id, message, timestamp)
        VALUES (?, ?, ?)
        """, (chat.project_id, chat.message, chat.timestamp))

    def get_project(self, project_id: str) -> Project:
        result = self.conn.execute("""
        SELECT * FROM projects WHERE project_id = ?
        """, (project_id,)).fetchone()
        
        if result:
            project = Project(*result)
            project.chats = self.get_chats(project.id)
            return project
        return None

    def get_chats(self, project_id: int) -> List[Chat]:
        results = self.conn.execute("""
        SELECT * FROM chats WHERE project_id = ?
        """, (project_id,)).fetchall()
        
        return [Chat(*row) for row in results]

    def close(self):
        self.conn.close()

# Example usage
if __name__ == "__main__":
    db = ProjectDB()
    
    # Create and insert a new project
    new_project = Project(session_id="session123", project_id="project456", owner="John Doe")
    db.insert_project(new_project)
    
    # Add a chat to the project
    new_chat = Chat(project_id=new_project.id, message="Hello, this is the first message!")
    db.insert_chat(new_chat)
    
    # Retrieve the project and its chats
    retrieved_project = db.get_project("project456")
    if retrieved_project:
        print(f"Retrieved project: {retrieved_project}")
        print(f"Chats: {retrieved_project.chats}")
    
    db.close()