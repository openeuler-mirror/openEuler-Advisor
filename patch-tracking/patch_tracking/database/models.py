"""
module of database model
"""
from patch_tracking.database import db


class Tracking(db.Model):
    """
    database model of tracking
    """
    id = db.Column(db.Integer, autoincrement=True)
    version_control = db.Column(db.String(80))
    scm_repo = db.Column(db.String(80))
    scm_branch = db.Column(db.String(80))
    scm_commit = db.Column(db.String(80))
    repo = db.Column(db.String(80), primary_key=True)
    branch = db.Column(db.String(80), primary_key=True)
    enabled = db.Column(db.Boolean)

    def __init__(self, version_control, scm_repo, scm_branch, scm_commit, repo, branch, enabled=True):
        self.version_control = version_control
        self.scm_repo = scm_repo
        self.scm_branch = scm_branch
        self.scm_commit = scm_commit
        self.repo = repo
        self.branch = branch
        self.enabled = enabled

    def __repr__(self):
        return '<Tracking %r %r>' % (self.repo, self.branch)

    def to_json(self):
        """
        convert to json
        """
        return {
            'version_control': self.version_control,
            'scm_repo': self.scm_repo,
            'scm_branch': self.scm_branch,
            'scm_commit': self.scm_commit,
            'repo': self.repo,
            'branch': self.branch,
            'enabled': self.enabled
        }


class Issue(db.Model):
    """
    database model of issue
    """
    issue = db.Column(db.String(80), primary_key=True)
    repo = db.Column(db.String(80))
    branch = db.Column(db.String(80))

    def __init__(self, issue, repo, branch):
        self.issue = issue
        self.repo = repo
        self.branch = branch

    def __repr__(self):
        return '<Issue %r %r %r>' % (self.issue, self.repo, self.branch)

    def to_json(self):
        """
        convert to json
        """
        return {'issue': self.issue, 'repo': self.repo, 'branch': self.branch}
