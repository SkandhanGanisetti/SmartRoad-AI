def verify_coverage(before, after):
    # A zero baseline cannot support a meaningful percentage comparison.
    if before <= 0:
        return {'improvement_percent': 0.0, 'status': 'Needs Review', 'notes': 'No measurable baseline damage was detected in the before image. A model checkpoint and clearer before image may be required; this heuristic cannot verify the repair.'}
    improvement = round((before-after)/before*100, 1)
    status = 'Verified' if improvement >= 35 and after <= 2.0 else 'Needs Review'
    reason = 'The reduction is significant and residual detected coverage is low.' if status == 'Verified' else 'A significant reduction and low residual detected coverage are both required.'
    return {'improvement_percent': improvement, 'status': status, 'notes': f'Estimated visible damage coverage changed from {before:.2f}% to {after:.2f}% ({improvement:.1f}% improvement). {reason} This is an image-based project heuristic.'}
