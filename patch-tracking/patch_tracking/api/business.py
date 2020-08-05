"""
api action method
"""
from sqlalchemy import and_
from patch_tracking.database import db
from patch_tracking.database.models import Tracking, Issue


def create_tracking(data):
    """
    create tracking
    """
    version_control = data.get("version_control")
    scm_repo = data.get('scm_repo')
    scm_branch = data.get('scm_branch')
    scm_commit = data.get('scm_commit')
    repo = data.get('repo')
    branch = data.get('branch')
    enabled = data.get('enabled')
    tracking = Tracking(version_control, scm_repo, scm_branch, scm_commit, repo, branch, enabled)
    db.session.add(tracking)
    db.session.commit()


def update_tracking(data):
    """
    update tracking
    """
    repo = data.get('repo')
    branch = data.get('branch')
    tracking = Tracking.query.filter(and_(Tracking.repo == repo, Tracking.branch == branch)).one()
    tracking.version_control = data.get("version_control")
    tracking.scm_repo = data.get('scm_repo')
    tracking.scm_branch = data.get('scm_branch')
    tracking.scm_commit = data.get('scm_commit')
    tracking.enabled = data.get('enabled')
    db.session.commit()


def delete_tracking(repo_, branch_=None):
    """
    delete tracking
    """
    if branch_:
        Tracking.query.filter(Tracking.repo == repo_, Tracking.branch == branch_).delete()
    else:
        Tracking.query.filter(Tracking.repo == repo_).delete()
    db.session.commit()


def create_issue(data):
    """
    create issue
    """
    issue = data.get('issue')
    repo = data.get('repo')
    branch = data.get('branch')
    issue_ = Issue(issue, repo, branch)
    db.session.add(issue_)
    db.session.commit()


def update_issue(data):
    """
    update issue
    """
    issue = data.get('issue')
    issue_ = Issue.query.filter(Issue.issue == issue).one()
    issue_.issue = data.get('issue')
    db.session.add(issue_)
    db.session.commit()


def delete_issue(issue):
    """
    delete issue
    """
    issue_ = Issue.query.filter(Issue.issue == issue).one()
    db.session.delete(issue_)
    db.session.commit()
